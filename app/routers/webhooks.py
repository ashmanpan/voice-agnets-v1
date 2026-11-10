"""Telephony webhooks: Twilio (TwiML + call status) and LiveKit call events.
These are called by external providers and are intentionally not behind the
API-key auth (they live under /twilio and /livekit, not /api)."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, Response, HTMLResponse
from sqlalchemy.orm import Session

from models import get_db, Contact, Call, TranscriptSegment, CallAnalysis
from twilio_handler import (
    generate_twiml_response,
    process_user_response,
    update_call_status,
)
from call_analyzer import CallAnalyzer

router = APIRouter()


@router.post("/twilio/call-status")
async def twilio_call_status(
    request: Request,
    call_id: int,
    step_id: Optional[str] = "greeting",
    db: Session = Depends(get_db)
):
    """Handle call status webhook from Twilio"""
    form_data = await request.form()
    call_status = form_data.get("CallStatus")

    # Update call status
    if call_status in ["ringing", "in-progress", "completed"]:
        update_call_status(db, call_id, call_status)

    # Generate TwiML response for current step
    twiml = generate_twiml_response(call_id, step_id, db)

    return Response(content=twiml, media_type="application/xml")


@router.post("/twilio/process-response")
async def twilio_process_response(
    request: Request,
    call_id: int,
    step_id: str,
    db: Session = Depends(get_db)
):
    """Process user's speech response with AI"""
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "")
    recording_url = form_data.get("RecordingUrl", "")

    # Process the response with AI
    next_action = await process_user_response(
        db, call_id, step_id, speech_result, recording_url
    )

    # Generate TwiML based on next action
    from twilio.twiml.voice_response import VoiceResponse

    if next_action["action"] == "hangup":
        response = VoiceResponse()
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    elif next_action["action"] == "ai_response":
        # NEW APPROACH: Use Twilio REST API to update call instead of returning TwiML
        from twilio.rest import Client
        import os

        ai_response_text = next_action.get("response_text", "")
        next_step_id = next_action.get("next_step_id", step_id)

        print(f"\n{'='*80}")
        print(f"[WEBHOOK /process-response] Call {call_id} - REST API UPDATE MODE")
        print(f"  AI response: {ai_response_text[:100]}...")
        print(f"  Using Twilio REST API to update call mid-flight")
        print(f"{'='*80}\n")

        # Get the call's Twilio SID
        call_record = db.query(Call).filter(Call.id == call_id).first()
        twilio_sid = call_record.twilio_call_sid

        # Use Twilio REST API to redirect the call to play AI response
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        public_url = os.getenv("PUBLIC_URL")

        client = Client(account_sid, auth_token)

        try:
            # Update the call to redirect to our AI response endpoint
            client.calls(twilio_sid).update(
                url=f"{public_url}/twilio/play-ai-dynamic?call_id={call_id}&step_id={next_step_id}",
                method="POST"
            )

            print(f"[WEBHOOK /process-response] ✓ Call updated via REST API")
            print(f"  Redirected to: /twilio/play-ai-dynamic?call_id={call_id}&step_id={next_step_id}")
            print(f"{'='*80}\n")

        except Exception as e:
            print(f"[WEBHOOK /process-response] ❌ Error updating call: {e}")
            print(f"{'='*80}\n")

        # Return empty TwiML (the update handles the redirect)
        from twilio.twiml.voice_response import VoiceResponse
        response = VoiceResponse()
        return Response(content=str(response), media_type="application/xml")

    elif next_action["action"] == "next_step":
        next_step_id = next_action["next_step_id"]
        twiml = generate_twiml_response(call_id, next_step_id, db)
        return Response(content=twiml, media_type="application/xml")


@router.post("/twilio/play-ai-response")
@router.get("/twilio/play-ai-response")
async def twilio_play_ai_response(
    call_id: int,
    step_id: str,
    db: Session = Depends(get_db)
):
    """Play the AI response that was generated in process_user_response"""
    from twilio.twiml.voice_response import VoiceResponse, Gather
    from call_scripts import get_script

    print(f"\n{'='*80}")
    print(f"[WEBHOOK /play-ai-response] Call {call_id} - Retrieving AI response from transcript")
    print(f"{'='*80}\n")

    # Get the most recent AI response from the transcript
    last_agent_segment = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.call_id == call_id)
        .filter(TranscriptSegment.speaker == "agent")
        .order_by(TranscriptSegment.sequence_number.desc())
        .first()
    )

    if not last_agent_segment:
        print(f"[WEBHOOK /play-ai-response] ⚠️ No AI response found in transcript!")
        response = VoiceResponse()
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    ai_response_text = last_agent_segment.text
    print(f"[WEBHOOK /play-ai-response] ✓ Found AI response: {ai_response_text[:100]}...")

    call = db.query(Call).filter(Call.id == call_id).first()
    script = get_script(call.call_type)

    # Find the current step
    current_step = None
    for step in script["steps"]:
        if step["id"] == step_id:
            current_step = step
            break

    response = VoiceResponse()

    if current_step and current_step.get("wait_for_response"):
        # Create Gather with AI response inside
        gather = Gather(
            input="speech",
            timeout=current_step.get("max_wait_seconds", 20),
            action=f"{os.getenv('PUBLIC_URL')}/twilio/process-response?call_id={call_id}&step_id={step_id}",
            method="POST"
        )
        gather.say(ai_response_text, voice="Polly.Joanna", language="en-US")
        response.append(gather)

        # If no input, handle appropriately
        response.redirect(f"{os.getenv('PUBLIC_URL')}/twilio/no-response?call_id={call_id}&step_id={step_id}")
    else:
        # Just say it and move on or hangup
        response.say(ai_response_text, voice="Polly.Joanna", language="en-US")
        response.hangup()

    print(f"[WEBHOOK /play-ai-response] 📤 Returning TwiML with AI response")
    return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/play-ai-dynamic")
@router.get("/twilio/play-ai-dynamic")
async def twilio_play_ai_dynamic(
    call_id: int,
    step_id: str,
    db: Session = Depends(get_db)
):
    """Play AI response - called via REST API update (not Gather action callback)"""
    from twilio.twiml.voice_response import VoiceResponse, Gather
    from call_scripts import get_script

    print(f"\n{'='*80}")
    print(f"[WEBHOOK /play-ai-dynamic] Call {call_id} - REST API REDIRECT MODE")
    print(f"  This endpoint was called via Twilio REST API update, not Gather action")
    print(f"{'='*80}\n")

    # Get the most recent AI response from transcript
    last_agent_segment = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.call_id == call_id)
        .filter(TranscriptSegment.speaker == "agent")
        .order_by(TranscriptSegment.sequence_number.desc())
        .first()
    )

    if not last_agent_segment:
        print(f"[WEBHOOK /play-ai-dynamic] ⚠️ No AI response found!")
        response = VoiceResponse()
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    ai_response_text = last_agent_segment.text
    print(f"[WEBHOOK /play-ai-dynamic] ✓ Found AI response: {ai_response_text[:100]}...")

    call = db.query(Call).filter(Call.id == call_id).first()
    script = get_script(call.call_type)

    # Find the current step
    current_step = None
    for step in script["steps"]:
        if step["id"] == step_id:
            current_step = step
            break

    response = VoiceResponse()

    # Say the AI response
    response.say(ai_response_text, voice="Polly.Joanna", language="en-US")

    # If we need to wait for user response, add Gather
    if current_step and current_step.get("wait_for_response"):
        gather = Gather(
            input="speech",
            timeout=current_step.get("max_wait_seconds", 20),
            action=f"{os.getenv('PUBLIC_URL')}/twilio/process-response?call_id={call_id}&step_id={step_id}",
            method="POST"
        )
        response.append(gather)
        response.redirect(f"{os.getenv('PUBLIC_URL')}/twilio/no-response?call_id={call_id}&step_id={step_id}")
    else:
        response.hangup()

    twiml_str = str(response)
    print(f"[WEBHOOK /play-ai-dynamic] 📤 Returning TwiML:")
    print(twiml_str)
    print(f"{'='*80}\n")

    return Response(content=twiml_str, media_type="application/xml")


@router.post("/twilio/no-response")
async def twilio_no_response(
    call_id: int,
    step_id: str,
    db: Session = Depends(get_db)
):
    """Handle when user doesn't respond"""
    from twilio.twiml.voice_response import VoiceResponse
    from twilio_handler import get_next_step, get_script

    call = db.query(Call).filter(Call.id == call_id).first()
    script = get_script(call.call_type)
    next_step = get_next_step(script, step_id)

    if next_step:
        twiml = generate_twiml_response(call_id, next_step["id"], db)
        return Response(content=twiml, media_type="application/xml")
    else:
        response = VoiceResponse()
        response.hangup()
        return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/call-ended")
async def twilio_call_ended(
    request: Request,
    call_id: int,
    db: Session = Depends(get_db)
):
    """Handle call ended webhook"""
    form_data = await request.form()

    call_duration = form_data.get("CallDuration")
    recording_url = form_data.get("RecordingUrl")

    update_call_status(
        db,
        call_id,
        "completed",
        ended_at=datetime.utcnow(),
        duration=int(call_duration) if call_duration else None,
        recording_url=recording_url
    )

    # Automatically analyze the call after it completes
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if call and call.status == "completed":
            analyzer = CallAnalyzer()
            analyzer.analyze_call(call, db)
            print(f"✓ Auto-analyzed call {call_id}")
    except Exception as e:
        print(f"⚠️  Failed to auto-analyze call {call_id}: {e}")

    return {"status": "ok"}




@router.post("/livekit/webhook")
async def livekit_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle LiveKit webhooks for call events
    CRITICAL: Analysis runs AFTER call ends to preserve zero-latency performance
    """
    import threading

    try:
        data = await request.json()
        event_type = data.get("event")

        # Only process room_finished events (when call ends)
        if event_type == "room_finished":
            room_name = data.get("room", {}).get("name", "")

            # Extract call_id from room name (format: call-123)
            if room_name.startswith("call-"):
                call_id = int(room_name.split("-")[1])

                # Update call status
                call = db.query(Call).filter(Call.id == call_id).first()
                if call:
                    call.status = "completed"
                    call.ended_at = datetime.utcnow()

                    # Calculate duration if started_at exists
                    if call.started_at:
                        duration = (call.ended_at - call.started_at).total_seconds()
                        call.duration = int(duration)

                    db.commit()

                    print(f"✅ Call {call_id} completed - starting analysis in background")

                    # BACKGROUND ANALYSIS - Zero impact on call latency
                    # Run analysis in separate thread to not block webhook response
                    def analyze_in_background():
                        from models import SessionLocal
                        from call_analyzer import CallAnalyzer

                        # Create new database session for background thread
                        bg_db = SessionLocal()
                        try:
                            bg_call = bg_db.query(Call).filter(Call.id == call_id).first()
                            if bg_call:
                                analyzer = CallAnalyzer()
                                analyzer.analyze_call(bg_call, bg_db)
                                print(f"✅ Background analysis completed for call {call_id}")
                        except Exception as e:
                            print(f"⚠️  Background analysis failed for call {call_id}: {e}")
                        finally:
                            bg_db.close()

                    # Start analysis thread (non-blocking)
                    analysis_thread = threading.Thread(target=analyze_in_background)
                    analysis_thread.daemon = True
                    analysis_thread.start()

        return {"status": "ok"}

    except Exception as e:
        print(f"⚠️  LiveKit webhook error: {e}")
        return {"status": "error", "message": str(e)}


