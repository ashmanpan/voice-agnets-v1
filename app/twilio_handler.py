"""
Twilio integration for making calls and handling webhooks
Enhanced with Groq AI for dynamic conversations
"""
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from datetime import datetime
from sqlalchemy.orm import Session
from models import Call, TranscriptSegment, Contact
from call_scripts import get_script, format_script_text
from speech_services import speech_to_text, analyze_sentiment
from groq_service import (
    generate_conversation_response,
    analyze_user_response,
    generate_dynamic_response
)
import asyncio

# Initialize Twilio client
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
public_url = os.getenv("PUBLIC_URL", "http://localhost:8000")

twilio_client = Client(account_sid, auth_token)


def initiate_call(db: Session, call_id: int):
    """
    Initiate an outbound call via Twilio

    Args:
        db: Database session
        call_id: ID of the call record

    Returns:
        Twilio call SID
    """
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise ValueError(f"Call {call_id} not found")

    contact = db.query(Contact).filter(Contact.id == call.contact_id).first()
    if not contact:
        raise ValueError(f"Contact {call.contact_id} not found")

    try:
        # Initiate call via Twilio
        twilio_call = twilio_client.calls.create(
            to=contact.phone_number,
            from_=twilio_phone,
            url=f"{public_url}/twilio/call-status?call_id={call_id}",
            status_callback=f"{public_url}/twilio/call-ended?call_id={call_id}",
            status_callback_event=["completed"],
            record=True  # Record the call
        )

        # Update call record
        call.twilio_call_sid = twilio_call.sid
        call.status = "dialing"
        call.started_at = datetime.utcnow()
        db.commit()

        return twilio_call.sid
    except Exception as e:
        call.status = "failed"
        db.commit()
        raise e


def generate_twiml_response(call_id: int, step_id: str, db: Session) -> str:
    """
    Generate TwiML response for a specific call step

    Args:
        call_id: Call ID
        step_id: Current step ID in the script
        db: Database session

    Returns:
        TwiML XML string
    """
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        return str(VoiceResponse())

    contact = db.query(Contact).filter(Contact.id == call.contact_id).first()
    script = get_script(call.call_type)

    # Find current step
    current_step = None
    for step in script["steps"]:
        if step["id"] == step_id:
            current_step = step
            break

    if not current_step:
        # End call if step not found
        response = VoiceResponse()
        response.hangup()
        return str(response)

    response = VoiceResponse()

    # Handle different actions
    if current_step.get("action") == "hangup":
        response.hangup()
        return str(response)

    # Check if this step has a message to say
    if "agent_says" in current_step:
        # Use custom greeting if provided, otherwise use script default
        if step_id == "greeting" and call.custom_greeting:
            agent_text = call.custom_greeting
        else:
            # Format the agent's message
            agent_text = format_script_text(
                current_step["agent_says"],
                contact_name=contact.name if contact else "there",
                custom_message=call.custom_message or "",
                caller_name=call.caller_name or "Krishnaji's CTO office",
                custom_subject=call.custom_subject or "testing the phone system"
            )

        # Save agent's message to transcript
        save_transcript_segment(db, call_id, "agent", agent_text)

        # Generate speech and play it
        response.say(agent_text, voice="Polly.Joanna", language="en-US")
    elif current_step.get("use_ai"):
        # For AI conversation steps, retrieve the most recent AI response from transcript
        # This happens when we redirect back here after generating an AI response
        print(f"\n[CALL {call_id}] 🔍 AI step with no agent_says - checking for recent AI response in transcript")

        last_agent_segment = (
            db.query(TranscriptSegment)
            .filter(TranscriptSegment.call_id == call_id)
            .filter(TranscriptSegment.speaker == "agent")
            .order_by(TranscriptSegment.sequence_number.desc())
            .first()
        )

        if last_agent_segment:
            agent_text = last_agent_segment.text
            print(f"[CALL {call_id}] ✓ Found recent AI response: {agent_text}")
            print(f"[CALL {call_id}] 📢 Playing AI response to user via TwiML")

            # Play the AI response
            response.say(agent_text, voice="Polly.Joanna", language="en-US")
        else:
            print(f"[CALL {call_id}] ⚠️ No AI response found in transcript - this shouldn't happen!")
            pass

    # Wait for response if needed
    if current_step.get("wait_for_response"):
        gather = Gather(
            input="speech",
            timeout=current_step.get("max_wait_seconds", 5),
            action=f"{public_url}/twilio/process-response?call_id={call_id}&step_id={step_id}",
            method="POST"
        )
        response.append(gather)

        # If no input, move to next step or end
        response.redirect(f"{public_url}/twilio/no-response?call_id={call_id}&step_id={step_id}")
    else:
        # Move to next step
        next_step = get_next_step(script, step_id)
        if next_step:
            response.redirect(f"{public_url}/twilio/call-status?call_id={call_id}&step_id={next_step['id']}")
        else:
            response.hangup()

    twiml_str = str(response)
    print(f"\n[generate_twiml_response] TwiML for call {call_id}, step '{step_id}':")
    print(twiml_str)
    print(f"{'='*80}\n")

    return twiml_str


def get_next_step(script: dict, current_step_id: str):
    """Get the next step in the script"""
    steps = script["steps"]

    # First check if current step has explicit next_step property
    for step in steps:
        if step["id"] == current_step_id:
            if "next_step" in step:
                # Find the step with matching ID
                next_step_id = step["next_step"]
                for next_step in steps:
                    if next_step["id"] == next_step_id:
                        return next_step
            # Otherwise return next step by position
            current_index = steps.index(step)
            if current_index + 1 < len(steps):
                return steps[current_index + 1]

    return None


def save_transcript_segment(db: Session, call_id: int, speaker: str, text: str):
    """Save a transcript segment to the database"""
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


def get_conversation_history(db: Session, call_id: int) -> list:
    """
    Get conversation history for AI context

    Returns:
        List of {"role": "user"/"assistant", "content": "text"}
    """
    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.call_id == call_id)
        .order_by(TranscriptSegment.sequence_number)
        .all()
    )

    history = []
    for seg in segments:
        role = "assistant" if seg.speaker == "agent" else "user"
        history.append({
            "role": role,
            "content": seg.text
        })

    return history


async def process_user_response(
    db: Session,
    call_id: int,
    step_id: str,
    speech_result: str,
    recording_url: str = None
) -> dict:
    """
    Process user's speech response with AI
    Uses Groq for intelligent, dynamic responses

    Args:
        db: Database session
        call_id: Call ID
        step_id: Current step ID
        speech_result: Transcribed speech
        recording_url: URL to recording

    Returns:
        Next action dict with AI-generated response
    """
    call = db.query(Call).filter(Call.id == call_id).first()
    contact = db.query(Contact).filter(Contact.id == call.contact_id).first()
    script = get_script(call.call_type)

    # Find current step
    current_step = None
    for step in script["steps"]:
        if step["id"] == step_id:
            current_step = step
            break

    if not current_step:
        return {"action": "hangup"}

    # Save user response to transcript
    if speech_result:
        print(f"\n{'='*80}")
        print(f"[CALL {call_id}] USER SPOKE on step '{step_id}':")
        print(f"  Raw speech: {speech_result}")
        print(f"{'='*80}\n")

        save_transcript_segment(db, call_id, "user", speech_result)

        # Get conversation history for AI context
        conversation_history = get_conversation_history(db, call_id)
        print(f"[CALL {call_id}] Conversation history retrieved:")
        for i, msg in enumerate(conversation_history):
            print(f"  {i+1}. {msg['role']}: {msg['content'][:100]}...")

        # Check if we're in AI conversation mode (only for steps marked with use_ai)
        if current_step.get("use_ai"):
            print(f"\n[CALL {call_id}] ✓ Step '{step_id}' has use_ai=True")
            # Count how many turns we've had
            turn_count = len([seg for seg in conversation_history if seg["role"] == "user"])
            max_turns = script.get("max_conversation_turns", 5)

            # Get system prompt for AI
            system_prompt = script.get(
                "conversation_system_prompt",
                "You are a friendly AI assistant. Have a natural conversation. Keep responses brief (1-2 sentences)."
            )

            print(f"[CALL {call_id}] Turn count: {turn_count}/{max_turns}")

            # Check if we should end the conversation
            if turn_count >= max_turns:
                print(f"[CALL {call_id}] ❌ Max turns reached, ending conversation")
                # Move to closing
                next_step_id = current_step.get("next_step", "closing")
                return {"action": "next_step", "next_step_id": next_step_id}

            print(f"[CALL {call_id}] 📤 Sending to Groq AI:")
            print(f"  System prompt: {system_prompt[:100]}...")
            print(f"  Conversation history: {len(conversation_history)} messages")

            # Generate AI response using full conversation history
            ai_response = generate_conversation_response(
                conversation_history,
                system_prompt=system_prompt
            )

            print(f"\n[CALL {call_id}] 📥 Groq AI Response:")
            print(f"  AI said: {ai_response}")
            print(f"  Length: {len(ai_response)} chars")

            # Save AI response to transcript
            save_transcript_segment(db, call_id, "agent", ai_response)
            print(f"[CALL {call_id}] ✓ Saved AI response to transcript")

            # Determine next step:
            # - If on ai_conversation step, stay on it to loop (don't transition yet)
            # - For other steps (like greeting), use next_step to transition to ai_conversation
            if step_id == "ai_conversation":
                next_step_id = "ai_conversation"  # Stay on ai_conversation to continue loop
            else:
                next_step_id = current_step.get("next_step", step_id)  # Transition (greeting -> ai_conversation)

            print(f"\n[CALL {call_id}] 🔄 Returning action:")
            print(f"  action: ai_response")
            print(f"  next_step_id: {next_step_id}")
            print(f"  continue_conversation: True")
            print(f"{'='*80}\n")

            # Return AI-generated response and continue conversation
            return {
                "action": "ai_response",
                "response_text": ai_response,
                "next_step_id": next_step_id,
                "continue_conversation": True
            }

        # For facility test, use AI to analyze response (old logic for non-conversational mode)
        if call.call_type == "facility_test" and step_id == "explain_test":
            keywords_positive = current_step.get("keywords_positive", [])
            keywords_negative = current_step.get("keywords_negative", [])

            # Use Groq AI for sentiment analysis (more accurate than keywords)
            sentiment = analyze_user_response(speech_result, keywords_positive, keywords_negative)

            if sentiment == "positive":
                next_step_id = "positive_closing"
                call.test_result = "PASS"
            elif sentiment == "negative":
                next_step_id = "ask_details"
                call.test_result = "FAIL"
            else:
                next_step_id = "positive_closing"
                call.test_result = "PASS"

            db.commit()
            return {"action": "next_step", "next_step_id": next_step_id}

        # For follow-up questions/responses, use AI to generate dynamic responses
        if step_id in ["ask_for_response", "ask_details"]:
            # Generate AI response based on conversation context
            context = {
                "name": contact.name if contact else "there",
                "message": call.custom_message or "",
                "call_type": call.call_type
            }

            ai_response = generate_dynamic_response(speech_result, context)

            # Save AI response to transcript
            save_transcript_segment(db, call_id, "agent", ai_response)

            # Return AI-generated response
            return {
                "action": "ai_response",
                "response_text": ai_response,
                "next_step_id": "closing"
            }

    # Default: move to next step (for initial greeting, etc.)
    next_step = get_next_step(script, step_id)
    if next_step:
        # Check for mark_test_result
        if next_step.get("mark_test_result"):
            call.test_result = next_step["mark_test_result"]
            db.commit()

        return {"action": "next_step", "next_step_id": next_step["id"]}
    else:
        return {"action": "hangup"}


def update_call_status(db: Session, call_id: int, status: str, **kwargs):
    """Update call status and other fields"""
    call = db.query(Call).filter(Call.id == call_id).first()
    if call:
        call.status = status
        for key, value in kwargs.items():
            if hasattr(call, key):
                setattr(call, key, value)
        db.commit()
