"""
LiveKit Voice Agent with Groq LLM
Real-time voice conversations with sub-second latency
"""
import logging
import time
import os
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
)
from livekit.plugins import openai, silero, deepgram

# Database integration for transcript storage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

# Load environment variables
load_dotenv()

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://voiceagent:voiceagent@db:5432/voiceagent")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Latency tracking
latency_stats = {
    "stt_times": [],
    "llm_times": [],
    "tts_times": [],
    "total_times": [],
}


class VoiceAssistant(Agent):
    """Voice Assistant Agent - Optimized for low latency"""
    def __init__(self, system_prompt: str = None, max_turns: int = None) -> None:
        # Use custom system prompt or default
        if system_prompt is None:
            system_prompt = (
                "You are a friendly AI assistant making a test call. "
                "Speak naturally and conversationally. "
                "Have a good conversation with the person - ask them questions, "
                "discuss various topics, and engage meaningfully. "
                "Keep each response to 1-2 sentences. "
                "Only say goodbye when the conversation naturally ends or after several exchanges."
            )

        super().__init__(instructions=system_prompt)

        # Track conversation turns (non-blocking)
        self.max_turns = max_turns
        self.turn_count = 0


def prewarm(proc: JobProcess):
    """
    Prewarm function to load models before accepting jobs
    This reduces cold start latency
    """
    proc.userdata["vad"] = silero.VAD.load()


def save_transcript_segment_async(call_id: int, speaker: str, text: str):
    """
    Save transcript segment to database asynchronously (non-blocking)
    This runs in a separate thread to avoid adding latency to the call
    """
    import threading

    def _save():
        try:
            from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
            from sqlalchemy.ext.declarative import declarative_base

            Base = declarative_base()

            class TranscriptSegment(Base):
                __tablename__ = "transcript_segments"
                id = Column(Integer, primary_key=True)
                call_id = Column(Integer)  # No FK constraint in background thread
                speaker = Column(String(10), nullable=False)
                text = Column(Text, nullable=False)
                timestamp = Column(DateTime, default=datetime.utcnow)
                sequence_number = Column(Integer, nullable=False)

            db = SessionLocal()

            # Get current sequence number
            last_segment = (
                db.query(TranscriptSegment)
                .filter(TranscriptSegment.call_id == call_id)
                .order_by(TranscriptSegment.sequence_number.desc())
                .first()
            )

            sequence = (last_segment.sequence_number + 1) if last_segment else 1

            segment = TranscriptSegment(
                call_id=call_id,
                speaker=speaker,
                text=text,
                sequence_number=sequence,
                timestamp=datetime.utcnow()
            )
            db.add(segment)
            db.commit()
            db.close()

            logger.info(f"💾 Transcript saved: {speaker[:1]}: {text[:50]}...")
        except Exception as e:
            logger.error(f"Failed to save transcript segment: {e}")

    # Run in background thread to avoid blocking the call
    thread = threading.Thread(target=_save, daemon=True)
    thread.start()


def update_call_transcript(call_id: int):
    """
    Compile full transcript and save to calls.transcript field (non-blocking)
    """
    import threading

    def _update():
        try:
            from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
            from sqlalchemy.ext.declarative import declarative_base

            Base = declarative_base()

            class Call(Base):
                __tablename__ = "calls"
                id = Column(Integer, primary_key=True)
                transcript = Column(Text)
                ended_at = Column(DateTime)
                status = Column(String(20))

            class TranscriptSegment(Base):
                __tablename__ = "transcript_segments"
                id = Column(Integer, primary_key=True)
                call_id = Column(Integer)
                speaker = Column(String(10))
                text = Column(Text)
                sequence_number = Column(Integer)

            db = SessionLocal()

            # Get all transcript segments for this call
            segments = (
                db.query(TranscriptSegment)
                .filter(TranscriptSegment.call_id == call_id)
                .order_by(TranscriptSegment.sequence_number)
                .all()
            )

            # Compile full transcript
            transcript_lines = []
            for seg in segments:
                speaker_name = "Agent" if seg.speaker == "agent" else "User"
                transcript_lines.append(f"{speaker_name}: {seg.text}")

            full_transcript = "\n".join(transcript_lines)

            # Update call record
            call = db.query(Call).filter(Call.id == call_id).first()
            if call:
                call.transcript = full_transcript
                call.ended_at = datetime.utcnow()
                call.status = "completed"
                db.commit()

                logger.info(f"✅ Call {call_id} transcript compiled and saved ({len(segments)} segments)")

            db.close()
        except Exception as e:
            logger.error(f"Failed to update call transcript: {e}")

    # Run in background thread
    thread = threading.Thread(target=_update, daemon=True)
    thread.start()


def save_task_response(task_id: int, call_id: int):
    """
    Analyze conversation and save task response (non-blocking)
    Extracts answers from transcript and updates task status
    """
    import threading

    def _save():
        try:
            from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
            from sqlalchemy.ext.declarative import declarative_base
            import json

            Base = declarative_base()

            class Task(Base):
                __tablename__ = "tasks"
                id = Column(Integer, primary_key=True)
                contact_response = Column(Text)
                response_sentiment = Column(String(20))
                task_completed = Column(Boolean)
                status = Column(String(20))
                completed_at = Column(DateTime)
                call_attempts = Column(Integer)

            class TranscriptSegment(Base):
                __tablename__ = "transcript_segments"
                id = Column(Integer, primary_key=True)
                call_id = Column(Integer)
                speaker = Column(String(10))
                text = Column(Text)
                sequence_number = Column(Integer)

            db = SessionLocal()

            # Get all transcript segments
            segments = (
                db.query(TranscriptSegment)
                .filter(TranscriptSegment.call_id == call_id)
                .order_by(TranscriptSegment.sequence_number)
                .all()
            )

            if not segments:
                logger.warning(f"No transcript found for call {call_id}")
                db.close()
                return

            # Build conversation
            conversation = []
            user_responses = []
            for seg in segments:
                if seg.speaker == "user":
                    user_responses.append(seg.text)
                conversation.append(f"{'User' if seg.speaker == 'user' else 'Agent'}: {seg.text}")

            full_conversation = "\n".join(conversation)
            combined_responses = " ".join(user_responses)

            # Simple sentiment analysis (can be enhanced with AI later)
            sentiment = "neutral"
            positive_words = ["yes", "sure", "okay", "great", "good", "thanks", "appreciate"]
            negative_words = ["no", "can't", "won't", "not", "busy", "later", "problem"]

            lower_response = combined_responses.lower()
            if any(word in lower_response for word in positive_words):
                sentiment = "positive"
            elif any(word in lower_response for word in negative_words):
                sentiment = "negative"

            # Determine if task was completed based on conversation
            task_completed = sentiment == "positive" and len(user_responses) > 0

            # Update task
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.contact_response = combined_responses[:1000]  # Limit to 1000 chars
                task.response_sentiment = sentiment
                task.task_completed = task_completed
                task.status = "completed"
                task.completed_at = datetime.utcnow()
                task.call_attempts = (task.call_attempts or 0) + 1
                db.commit()

                logger.info(f"✅ Task {task_id} response saved - Sentiment: {sentiment}, Completed: {task_completed}")

            db.close()
        except Exception as e:
            logger.error(f"Failed to save task response: {e}")

    # Run in background thread
    thread = threading.Thread(target=_save, daemon=True)
    thread.start()


def load_task_from_database(call_id: int):
    """
    Load task details if this is a task delivery call
    Returns None if no task found or not a task delivery call
    """
    try:
        from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()

        class Call(Base):
            __tablename__ = "calls"
            id = Column(Integer, primary_key=True)
            call_type = Column(String(20))

        class Task(Base):
            __tablename__ = "tasks"
            id = Column(Integer, primary_key=True)
            assigned_call_id = Column(Integer)
            title = Column(String(200))
            description = Column(Text)
            task_type = Column(String(50))
            agent_script = Column(Text)
            questions_to_ask = Column(Text)
            collect_response = Column(Boolean, default=True)
            status = Column(String(20))

        db = SessionLocal()

        # Check if this call is a task delivery
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call or call.call_type != "task_delivery":
            db.close()
            return None

        # Find the task linked to this call
        task = db.query(Task).filter(Task.assigned_call_id == call_id).first()
        if not task:
            db.close()
            return None

        # Update task status to in_progress
        task.status = "in_progress"
        db.commit()

        # Return task details as dict
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "agent_script": task.agent_script,
            "questions_to_ask": task.questions_to_ask,
            "collect_response": task.collect_response
        }

        db.close()
        logger.info(f"📋 Task loaded: {task.title} (ID: {task.id})")
        return task_data

    except Exception as e:
        logger.error(f"Failed to load task: {e}")
        return None


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the voice agent

    This sets up the STT-LLM-TTS pipeline and starts the agent
    Handles both inbound and outbound calls
    NOW WITH TASK DELIVERY SUPPORT (DROP 2)
    """
    import json
    from livekit import api
    from livekit.agents import stt, llm, tts

    logger.info(f"connecting to room {ctx.room.name}")

    # Track start time
    session_start_time = time.time()

    # Check if this is an outbound call (phone number in metadata)
    phone_number = None
    sip_trunk_id = None
    call_id = None
    contact_name = None
    custom_greeting = None
    caller_name = None
    system_prompt = None
    max_turns = None
    task_data = None  # NEW: Task data for task delivery calls

    try:
        if ctx.job.metadata:
            metadata = json.loads(ctx.job.metadata)
            phone_number = metadata.get("phone_number")
            sip_trunk_id = metadata.get("sip_trunk_id")
            call_id = metadata.get("call_id")
            contact_name = metadata.get("contact_name")
            custom_greeting = metadata.get("greeting")
            caller_name = metadata.get("caller_name", "Krishnaji's CTO office")
            system_prompt = metadata.get("system_prompt")
            max_turns = metadata.get("max_turns", 8)  # Default to 8 turns like Twilio

            logger.info(f"Outbound call metadata: phone={phone_number}, call_id={call_id}, max_turns={max_turns}")
            if custom_greeting:
                logger.info(f"Custom greeting: {custom_greeting[:50]}...")

            # NEW: Load task if this is a task delivery call
            if call_id:
                task_data = load_task_from_database(call_id)
                if task_data:
                    logger.info(f"📋 This is a TASK DELIVERY call: {task_data['title']}")
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

    # NEW: Build task-aware system prompt if this is a task delivery call
    if task_data and not system_prompt:
        import json
        questions = json.loads(task_data['questions_to_ask']) if task_data['questions_to_ask'] else []
        questions_text = "\n".join([f"   {i+1}. {q}" for i, q in enumerate(questions)])

        system_prompt = f"""You are calling {contact_name} to discuss an important task.

Task: {task_data['title']}
Details: {task_data['description']}

Your objectives:
1. Greet them professionally and warmly
2. Explain the task clearly: {task_data['agent_script'] if task_data['agent_script'] else task_data['description']}
3. {"Ask these specific questions:" if questions else "Get their confirmation and thoughts."}
{questions_text if questions else ""}
4. Listen carefully to their responses
5. Confirm their understanding
6. Thank them and end the call

Important guidelines:
- Be conversational and friendly, not robotic
- Speak in 1-2 sentences at a time
- Give them time to respond
- If they have questions, answer them naturally
- Keep the call focused on the task
- Keep the call under 5 minutes

Remember: You're helping them with this task, not interrogating them."""

        logger.info(f"📋 Generated task-aware system prompt for: {task_data['title']}")

    # Create voice assistant agent with custom settings
    assistant = VoiceAssistant(
        system_prompt=system_prompt,
        max_turns=max_turns
    )

    # Store task_data in assistant for later use in response collection
    assistant.task_data = task_data
    assistant.call_id = call_id

    # Create agent session with STT, LLM, and TTS using actual plugins
    # Optimized for ultra-low latency with GROQ (blazing fast LLM!)
    import os

    # Use Deepgram + Groq + OpenAI TTS for ultra-fast responses
    session = AgentSession(
        stt=deepgram.STT(model="nova-2"),  # Deepgram Nova-2: ~300ms latency
        llm=openai.LLM(
            model="llama-3.3-70b-versatile",  # Groq's fastest model (~500ms)
            temperature=0.7,
            base_url="https://api.groq.com/openai/v1",  # Groq API endpoint
            api_key=os.getenv("GROQ_API_KEY"),
        ),
        tts=openai.TTS(
            voice="alloy",
            speed=1.0,  # Normal speed - natural conversation
        ),
        vad=ctx.proc.userdata["vad"],  # Voice Activity Detection
    )

    # Add event handler for capturing conversation items (CORRECT LiveKit approach)
    @session.on("conversation_item_added")
    def on_conversation_item_added(event):
        """Capture all conversation items - both user and agent"""
        try:
            role = event.item.role  # 'user' or 'assistant'
            text_content = event.item.text_content

            if text_content:
                speaker = "user" if role == "user" else "agent"
                logger.info(f"{'👤' if role == 'user' else '🤖'} {role.capitalize()} said: {text_content}")

                # Save to transcript (non-blocking)
                if call_id:
                    save_transcript_segment_async(call_id, speaker, text_content)

                # Increment turn count for user messages (non-blocking check)
                if role == "user":
                    assistant.turn_count += 1
                    logger.info(f"🔢 Turn {assistant.turn_count}/{assistant.max_turns if assistant.max_turns else '∞'}")

                    if assistant.max_turns and assistant.turn_count >= assistant.max_turns:
                        logger.info(f"🛑 Max turns ({assistant.max_turns}) reached, ending conversation")
                        # Request agent to say goodbye and end (non-blocking)
                        import asyncio
                        asyncio.create_task(session.generate_reply(
                            instructions="Politely say goodbye and end the conversation now."
                        ))
        except Exception as e:
            logger.error(f"Error in conversation_item_added handler: {e}")

    # Start the session with the agent
    turn_start_time = {}

    @session.on("user_started_speaking")
    def on_user_start(ev):
        turn_start_time["user"] = time.time()
        logger.info("🎤 User started speaking")

    @session.on("agent_started_speaking")
    def on_agent_start(ev):
        if "user" in turn_start_time:
            response_time = (time.time() - turn_start_time["user"]) * 1000
            logger.info(f"⏱️  TOTAL RESPONSE LATENCY: {response_time:.0f}ms (from user speech end to agent speech start)")
            del turn_start_time["user"]
        logger.info("🔊 Agent started speaking")

    await session.start(
        agent=assistant,
        room=ctx.room,
    )

    logger.info("voice agent started successfully")

    # For outbound calls, generate greeting after call is answered
    if phone_number:
        greeting_start = time.time()

        # Use custom greeting or generate default
        if custom_greeting:
            greeting_text = custom_greeting
            logger.info(f"Using custom greeting: {greeting_text[:50]}...")
        else:
            # Generate default greeting
            if contact_name:
                greeting_text = f"Hello! This is an AI assistant calling from {caller_name}. May I speak with {contact_name}?"
            else:
                greeting_text = "Hello! This is a test call from an AI assistant."

        await session.generate_reply(
            instructions=f"Say: {greeting_text}"
        )
        greeting_time = (time.time() - greeting_start) * 1000
        logger.info(f"⏱️  Total greeting generation latency: {greeting_time:.0f}ms")

        # Save greeting to transcript (non-blocking)
        if call_id:
            save_transcript_segment_async(call_id, "agent", greeting_text)

    # Add disconnect handler to save transcript when call ends
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant):
        logger.info(f"👋 Participant disconnected: {participant.identity}")
        if call_id:
            logger.info(f"📝 Compiling and saving transcript for call {call_id}")
            update_call_transcript(call_id)

    # Also add shutdown callback to ensure transcript is saved
    def save_transcript_on_shutdown():
        if call_id:
            logger.info(f"🔚 Session ending, saving final transcript for call {call_id}")
            update_call_transcript(call_id)

            # NEW: Save task response if this was a task delivery call
            if task_data:
                logger.info(f"📋 Saving task response for task {task_data['id']}")
                save_task_response(task_data['id'], call_id)

    ctx.add_shutdown_callback(save_transcript_on_shutdown)


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
