"""
LiveKit Voice Agent with Groq LLM
Real-time voice conversations with sub-second latency
"""
import logging
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
)
from livekit.plugins import silero

# Load environment variables
load_dotenv()

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)


class VoiceAssistant(Agent):
    """Voice Assistant Agent"""
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly AI assistant making a test call. "
                "Have a natural conversation with the person. "
                "Ask them how they are, discuss the purpose of the call (testing the phone system), "
                "and engage in friendly small talk. "
                "Keep responses concise (1-2 sentences). "
                "After 4-5 exchanges, politely end the conversation."
            ),
        )


def prewarm(proc: JobProcess):
    """
    Prewarm function to load models before accepting jobs
    This reduces cold start latency
    """
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the voice agent

    This sets up the STT-LLM-TTS pipeline and starts the agent
    Handles both inbound and outbound calls
    """
    import json
    from livekit import api

    logger.info(f"connecting to room {ctx.room.name}")

    # Check if this is an outbound call (phone number in metadata)
    phone_number = None
    sip_trunk_id = None

    try:
        if ctx.job.metadata:
            metadata = json.loads(ctx.job.metadata)
            phone_number = metadata.get("phone_number")
            sip_trunk_id = metadata.get("sip_trunk_id")
            logger.info(f"Outbound call metadata: phone={phone_number}, trunk={sip_trunk_id}")
    except (json.JSONDecodeError, AttributeError) as e:
        logger.info(f"No metadata or not an outbound call: {e}")

    # Connect to the room
    await ctx.connect()

    # If this is an outbound call, create SIP participant to dial the number
    if phone_number and sip_trunk_id:
        logger.info(f"Initiating outbound call to {phone_number}")
        try:
            await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=ctx.room.name,
                    sip_trunk_id=sip_trunk_id,
                    sip_call_to=phone_number,
                    participant_identity=phone_number,
                )
            )
            logger.info(f"SIP participant created for {phone_number}")
        except Exception as e:
            logger.error(f"Failed to create SIP participant: {e}")
            await ctx.shutdown()
            return

    # Create agent session with STT, LLM, and TTS
    # Using string identifiers for model configuration
    session = AgentSession(
        stt="openai/whisper-1",  # OpenAI Whisper for speech-to-text
        llm="groq/llama-3.3-70b-versatile",  # Groq LLM for fast responses
        tts="openai/tts-1",  # OpenAI TTS for speech synthesis
        vad=ctx.proc.userdata["vad"],  # Voice Activity Detection
    )

    # Start the session with the assistant
    assistant = VoiceAssistant()

    await session.start(
        ctx.room,
        agent=assistant,
        greeting="Hello! This is an AI assistant calling from Krishnaji's CTO office. May I speak with you for a moment?"
    )

    logger.info("voice agent started successfully")


if __name__ == "__main__":
    """
    Start the LiveKit voice agent worker

    This will connect to LiveKit Cloud and wait for incoming calls
    """
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="voice-assistant",  # Name used by SIP dispatch rules
        ),
    )
