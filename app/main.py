"""
Voice Agent Main Application
FastAPI server with Twilio webhooks and web dashboard
"""
from fastapi import FastAPI, Request, Depends, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os
import csv
import io

from models import get_db, Contact, Call, TranscriptSegment, CallAnalysis
from twilio_handler import (
    initiate_call,
    generate_twiml_response,
    process_user_response,
    update_call_status
)
from scheduler_service import (
    start_scheduler,
    stop_scheduler,
    schedule_one_time_call,
    schedule_recurring_call,
    cancel_scheduled_call,
    pause_recurring_call,
    resume_recurring_call,
    cancel_recurring_call
)
from call_analyzer import CallAnalyzer
from daily_report import DailyReportGenerator

app = FastAPI(title="Voice Agent System")


# ========================
# LiveKit Call Initiation (Default for all calls)
# ========================

async def initiate_livekit_call(
    db: Session,
    call_id: int,
    phone_number: str,
    contact_name: str,
    custom_greeting: str = None,
    caller_name: str = None,
    system_prompt: str = None,
    max_turns: int = 8
):
    """
    Initiate a LiveKit call (1-3 second latency)
    This is now the default for ALL calls.
    """
    import json
    from livekit import api as livekit_api

    try:
        lk_api = livekit_api.LiveKitAPI(
            url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
        )

        room_name = f"call-{call_id}"

        # Prepare metadata for agent
        metadata = {
            "phone_number": phone_number,
            "contact_name": contact_name,
            "greeting": custom_greeting,
            "call_id": call_id,
            "caller_name": caller_name or "Krishnaji's CTO office",
            "sip_trunk_id": os.getenv("LIVEKIT_SIP_TRUNK_ID"),
            "system_prompt": system_prompt,
            "max_turns": max_turns
        }

        # Dispatch agent to room
        dispatch_response = await lk_api.agent_dispatch.create_dispatch(
            livekit_api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="voice-assistant",
                metadata=json.dumps(metadata)
            )
        )

        print(f"✅ LiveKit call initiated: Room={room_name}, Phone={phone_number}, Call ID={call_id}")

        # Update call record
        call = db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.livekit_room_name = room_name
            call.status = "in-progress"
            db.commit()

        return room_name

    except Exception as e:
        print(f"❌ LiveKit call failed: {e}")
        # Update call status to failed
        call = db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.status = "failed"
            db.commit()
        raise


# Start scheduler on application startup
@app.on_event("startup")
async def startup_event():
    start_scheduler()

# Stop scheduler on application shutdown
@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="static")


# ========================
# Web Dashboard Routes
# ========================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Main dashboard"""
    # Get recent calls
    recent_calls = (
        db.query(Call)
        .join(Contact)
        .order_by(Call.created_at.desc())
        .limit(10)
        .all()
    )

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "recent_calls": recent_calls}
    )


@app.post("/api/calls/personal-message")
async def create_personal_message_call(
    name: str = Form(...),
    phone: str = Form(...),
    message: str = Form(...),
    caller_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a personal message call using LiveKit (1-3s latency)"""
    # Create or get contact
    contact = db.query(Contact).filter(Contact.phone_number == phone).first()
    if not contact:
        contact = Contact(
            name=name,
            phone_number=phone,
            contact_type="friend"
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)

    # Create call record
    call = Call(
        contact_id=contact.id,
        call_type="personal_message",
        custom_message=message,
        custom_greeting=message,  # Use message as greeting
        caller_name=caller_name or "Krishnaji's CTO office",
        status="queued"
    )
    db.add(call)
    db.commit()
    db.refresh(call)

    # Initiate call with LiveKit (low latency)
    try:
        room_name = await initiate_livekit_call(
            db=db,
            call_id=call.id,
            phone_number=phone,
            contact_name=name,
            custom_greeting=message,
            caller_name=caller_name
        )
        return JSONResponse({
            "success": True,
            "call_id": call.id,
            "room_name": room_name,
            "message": "LiveKit call initiated (1-3s latency!)"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/calls/facility-test")
async def create_facility_test_call(
    name: str = Form(...),
    phone: str = Form(...),
    caller_name: str = Form(None),  # Optional: e.g., "Krishnaji's CTO office"
    custom_greeting: str = Form(None),  # Optional: custom greeting
    custom_subject: str = Form(None),  # Optional: subject of call
    db: Session = Depends(get_db)
):
    """Create a facility test call using LiveKit (1-3s latency)"""
    # Create or get contact
    contact = db.query(Contact).filter(Contact.phone_number == phone).first()
    if not contact:
        contact = Contact(
            name=name,
            phone_number=phone,
            contact_type="facility"
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)

    # Create call record
    call = Call(
        contact_id=contact.id,
        call_type="facility_test",
        status="queued",
        caller_name=caller_name or "Krishnaji's CTO office",  # Default
        custom_greeting=custom_greeting,
        custom_subject=custom_subject
    )
    db.add(call)
    db.commit()
    db.refresh(call)

    # Initiate call with LiveKit (low latency)
    try:
        room_name = await initiate_livekit_call(
            db=db,
            call_id=call.id,
            phone_number=phone,
            contact_name=name,
            custom_greeting=custom_greeting,
            caller_name=caller_name
        )
        return JSONResponse({
            "success": True,
            "call_id": call.id,
            "room_name": room_name,
            "message": "LiveKit test call initiated (1-3s latency!)"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/calls/livekit-call")
async def create_livekit_call(
    name: str = Form(...),
    phone: str = Form(...),
    custom_greeting: str = Form(None),
    caller_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Make a call using LiveKit (1-3 second latency vs 15-20 seconds with Twilio)"""
    import json
    from livekit import api as livekit_api

    # 1. Create or get contact
    contact = db.query(Contact).filter(Contact.phone_number == phone).first()
    if not contact:
        contact = Contact(
            name=name,
            phone_number=phone,
            contact_type="facility"
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)

    # 2. Create call record
    default_caller = caller_name or "Krishnaji's CTO office"
    default_greeting = f"Hello! This is an AI assistant calling from {default_caller}. May I speak with {name}?"

    call = Call(
        contact_id=contact.id,
        call_type="facility_test",
        status="queued",
        custom_greeting=custom_greeting or default_greeting,
        caller_name=default_caller
    )
    db.add(call)
    db.commit()
    db.refresh(call)

    # 3. Create LiveKit room and dispatch agent to make call
    try:
        lk_api = livekit_api.LiveKitAPI(
            url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
        )

        room_name = f"call-{call.id}"

        print(f"Dispatching LiveKit agent for {phone} in room {room_name}")

        # Prepare metadata for agent (agent will create SIP participant)
        metadata = {
            "phone_number": phone,
            "contact_name": name,
            "greeting": custom_greeting or call.custom_greeting,
            "call_id": call.id,
            "caller_name": caller_name or "Krishnaji's CTO office",
            "sip_trunk_id": os.getenv("LIVEKIT_SIP_TRUNK_ID")
        }

        # Dispatch agent to new room with metadata
        # This creates the room and dispatches the agent in one call
        dispatch_response = await lk_api.agent_dispatch.create_dispatch(
            livekit_api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="voice-assistant",  # Must match agent_name in agent.py
                metadata=json.dumps(metadata)
            )
        )

        print(f"✅ Agent dispatched to room: {room_name}")
        print(f"   Dispatch ID: {dispatch_response.id}")
        print(f"   Agent will call: {phone}")

        # Update call record
        call.livekit_room_name = room_name
        call.status = "in-progress"
        db.commit()

        print(f"✅ LiveKit call initiated: Room={room_name}, Phone={phone}")

        return JSONResponse({
            "success": True,
            "call_id": call.id,
            "room_name": room_name,
            "dispatch_id": dispatch_response.id,
            "message": "LiveKit call initiated (1-3s latency!)"
        })

    except Exception as e:
        call.status = "failed"
        db.commit()
        print(f"❌ LiveKit call failed: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/contacts/upload-csv")
async def upload_csv_contacts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload contacts via CSV file"""
    if not file.filename.endswith('.csv'):
        return JSONResponse({
            "success": False,
            "error": "File must be a CSV file"
        }, status_code=400)

    try:
        # Read CSV file
        contents = await file.read()
        csv_text = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))

        imported_count = 0
        skipped_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # start=2 because row 1 is header
            try:
                # Required fields
                name = row.get('name', '').strip()
                phone = row.get('phone', '').strip()

                if not name or not phone:
                    errors.append(f"Row {row_num}: Missing name or phone")
                    continue

                # Check if contact already exists
                existing_contact = db.query(Contact).filter(
                    Contact.phone_number == phone
                ).first()

                if existing_contact:
                    skipped_count += 1
                    continue

                # Optional fields
                email = row.get('email', '').strip() or None
                contact_type = row.get('contact_type', '').strip() or 'general'
                notes = row.get('notes', '').strip() or None

                # Create new contact
                contact = Contact(
                    name=name,
                    phone_number=phone,
                    email=email,
                    contact_type=contact_type,
                    notes=notes
                )
                db.add(contact)
                imported_count += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        # Commit all contacts
        db.commit()

        return JSONResponse({
            "success": True,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "errors": errors if errors else None,
            "message": f"Successfully imported {imported_count} contacts"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/calls/schedule")
async def schedule_call(
    name: str = Form(...),
    phone: str = Form(...),
    call_type: str = Form(...),  # 'facility_test' or 'personal_message'
    scheduled_time: str = Form(...),  # ISO format datetime string
    caller_name: str = Form(None),
    custom_greeting: str = Form(None),
    custom_subject: str = Form(None),
    custom_message: str = Form(None),  # For personal_message type
    db: Session = Depends(get_db)
):
    """Schedule a one-time call for a specific date/time"""
    try:
        # Parse scheduled time
        scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

        # Validate that scheduled time is in the future
        if scheduled_datetime <= datetime.utcnow():
            return JSONResponse({
                "success": False,
                "error": "Scheduled time must be in the future"
            }, status_code=400)

        # Create or get contact
        contact = db.query(Contact).filter(Contact.phone_number == phone).first()
        if not contact:
            contact = Contact(
                name=name,
                phone_number=phone,
                contact_type="general"
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)

        # Create scheduled call record
        call = Call(
            contact_id=contact.id,
            call_type=call_type,
            status="scheduled",
            caller_name=caller_name or "Krishnaji's CTO office",
            custom_greeting=custom_greeting,
            custom_subject=custom_subject,
            custom_message=custom_message,
            is_scheduled=True,
            scheduled_time=scheduled_datetime
        )
        db.add(call)
        db.commit()
        db.refresh(call)

        # Schedule the call
        schedule_one_time_call(call.id, scheduled_datetime)

        return JSONResponse({
            "success": True,
            "call_id": call.id,
            "scheduled_time": scheduled_datetime.isoformat(),
            "message": f"Call scheduled for {scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/calls/recurring")
async def create_recurring_call(
    name: str = Form(...),
    phone: str = Form(...),
    call_type: str = Form(...),
    recurrence_pattern: str = Form(...),  # 'daily', 'weekly', 'monthly'
    recurrence_time: str = Form(...),  # HH:MM format (e.g., "17:00" for 5pm)
    recurrence_day: str = Form(None),  # Day of week for weekly (e.g., "monday")
    caller_name: str = Form(None),
    custom_greeting: str = Form(None),
    custom_subject: str = Form(None),
    custom_message: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a recurring call schedule"""
    try:
        # Validate pattern
        if recurrence_pattern not in ['daily', 'weekly', 'monthly']:
            return JSONResponse({
                "success": False,
                "error": "Invalid recurrence pattern. Must be 'daily', 'weekly', or 'monthly'"
            }, status_code=400)

        # Validate time format
        try:
            hour, minute = map(int, recurrence_time.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except:
            return JSONResponse({
                "success": False,
                "error": "Invalid time format. Use HH:MM (e.g., '17:00')"
            }, status_code=400)

        # For weekly pattern, day is required
        if recurrence_pattern == 'weekly' and not recurrence_day:
            return JSONResponse({
                "success": False,
                "error": "Day of week is required for weekly pattern"
            }, status_code=400)

        # Create or get contact
        contact = db.query(Contact).filter(Contact.phone_number == phone).first()
        if not contact:
            contact = Contact(
                name=name,
                phone_number=phone,
                contact_type="general"
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)

        # Create recurring call record
        call = Call(
            contact_id=contact.id,
            call_type=call_type,
            status="scheduled",
            caller_name=caller_name or "Krishnaji's CTO office",
            custom_greeting=custom_greeting,
            custom_subject=custom_subject,
            custom_message=custom_message,
            is_recurring=True,
            recurrence_pattern=recurrence_pattern,
            recurrence_time=recurrence_time,
            recurrence_day=recurrence_day,
            is_active=True
        )
        db.add(call)
        db.commit()
        db.refresh(call)

        # Schedule the recurring call
        schedule_recurring_call(call.id, recurrence_pattern, recurrence_time, recurrence_day)

        # Build description
        if recurrence_pattern == 'daily':
            schedule_desc = f"every day at {recurrence_time}"
        elif recurrence_pattern == 'weekly':
            schedule_desc = f"every {recurrence_day} at {recurrence_time}"
        else:
            schedule_desc = f"monthly on day 1 at {recurrence_time}"

        return JSONResponse({
            "success": True,
            "call_id": call.id,
            "message": f"Recurring call scheduled {schedule_desc}"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/calls/{call_id}/cancel")
async def cancel_call(call_id: int, db: Session = Depends(get_db)):
    """Cancel a scheduled or recurring call"""
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            return JSONResponse({
                "success": False,
                "error": "Call not found"
            }, status_code=404)

        if call.is_recurring:
            cancel_recurring_call(call_id)
            call.is_active = False
        else:
            cancel_scheduled_call(call_id)
            call.status = "cancelled"

        db.commit()

        return JSONResponse({
            "success": True,
            "message": "Call cancelled successfully"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/calls/{call_id}/pause")
async def pause_call(call_id: int, db: Session = Depends(get_db)):
    """Pause a recurring call"""
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            return JSONResponse({
                "success": False,
                "error": "Call not found"
            }, status_code=404)

        if not call.is_recurring:
            return JSONResponse({
                "success": False,
                "error": "Only recurring calls can be paused"
            }, status_code=400)

        pause_recurring_call(call_id)
        call.is_active = False
        db.commit()

        return JSONResponse({
            "success": True,
            "message": "Recurring call paused"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/calls/{call_id}/resume")
async def resume_call(call_id: int, db: Session = Depends(get_db)):
    """Resume a paused recurring call"""
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            return JSONResponse({
                "success": False,
                "error": "Call not found"
            }, status_code=404)

        if not call.is_recurring:
            return JSONResponse({
                "success": False,
                "error": "Only recurring calls can be resumed"
            }, status_code=400)

        resume_recurring_call(call_id)
        call.is_active = True
        db.commit()

        return JSONResponse({
            "success": True,
            "message": "Recurring call resumed"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/calls/{call_id}")
async def get_call_details(call_id: int, db: Session = Depends(get_db)):
    """Get call details including transcript"""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    contact = db.query(Contact).filter(Contact.id == call.contact_id).first()

    # Get transcript segments
    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.call_id == call_id)
        .order_by(TranscriptSegment.sequence_number)
        .all()
    )

    return {
        "call": {
            "id": call.id,
            "status": call.status,
            "call_type": call.call_type,
            "started_at": call.started_at.isoformat() if call.started_at else None,
            "ended_at": call.ended_at.isoformat() if call.ended_at else None,
            "duration": call.duration,
            "test_result": call.test_result,
            "recording_url": call.recording_url
        },
        "contact": {
            "name": contact.name,
            "phone": contact.phone_number
        },
        "transcript": [
            {
                "speaker": seg.speaker,
                "text": seg.text,
                "timestamp": seg.timestamp.isoformat()
            }
            for seg in segments
        ]
    }


# ========================
# Twilio Webhook Routes
# ========================

@app.post("/twilio/call-status")
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


@app.post("/twilio/process-response")
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


@app.post("/twilio/play-ai-response")
@app.get("/twilio/play-ai-response")
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


@app.post("/twilio/play-ai-dynamic")
@app.get("/twilio/play-ai-dynamic")
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


@app.post("/twilio/no-response")
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


@app.post("/twilio/call-ended")
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


# ========================
# Call Analysis & Reports
# ========================

@app.post("/api/calls/{call_id}/analyze")
async def analyze_call(call_id: int, db: Session = Depends(get_db)):
    """Analyze a completed call and extract insights"""
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            return JSONResponse({
                "success": False,
                "error": "Call not found"
            }, status_code=404)

        if call.status != "completed":
            return JSONResponse({
                "success": False,
                "error": "Can only analyze completed calls"
            }, status_code=400)

        analyzer = CallAnalyzer()
        analysis = analyzer.analyze_call(call, db)

        if not analysis:
            return JSONResponse({
                "success": False,
                "error": "No transcript available to analyze"
            }, status_code=400)

        import json
        return JSONResponse({
            "success": True,
            "analysis": {
                "call_id": call_id,
                "summary": analysis.summary,
                "action_items": json.loads(analysis.action_items),
                "requests": json.loads(analysis.requests),
                "complaints": json.loads(analysis.complaints),
                "sentiment": analysis.sentiment,
                "call_outcome": analysis.call_outcome
            }
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/calls/{call_id}/analysis")
async def get_call_analysis(call_id: int, db: Session = Depends(get_db)):
    """Get existing analysis for a call"""
    try:
        analysis = db.query(CallAnalysis).filter(
            CallAnalysis.call_id == call_id
        ).first()

        if not analysis:
            return JSONResponse({
                "success": False,
                "error": "No analysis found for this call. Run /analyze first."
            }, status_code=404)

        import json
        return JSONResponse({
            "success": True,
            "analysis": {
                "call_id": call_id,
                "summary": analysis.summary,
                "action_items": json.loads(analysis.action_items),
                "requests": json.loads(analysis.requests),
                "complaints": json.loads(analysis.complaints),
                "sentiment": analysis.sentiment,
                "call_outcome": analysis.call_outcome,
                "analyzed_at": analysis.analyzed_at.isoformat()
            }
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/reports/daily")
async def generate_daily_report(
    date: Optional[str] = None,
    format: str = "json",  # 'json' or 'text'
    db: Session = Depends(get_db)
):
    """Generate daily report for all calls"""
    try:
        # Parse date if provided
        report_date = None
        if date:
            report_date = datetime.fromisoformat(date)

        generator = DailyReportGenerator(db)

        if format == "text":
            report_text = generator.generate_text_report(report_date)
            return Response(content=report_text, media_type="text/plain")
        else:
            report = generator.generate_report(report_date)
            return JSONResponse(report)

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/reports/summary")
async def generate_summary_report(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Generate summary report for last N days"""
    try:
        generator = DailyReportGenerator(db)
        report = generator.generate_summary_report(days)
        return JSONResponse(report)

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/analyze-all-calls")
async def analyze_all_calls(db: Session = Depends(get_db)):
    """Analyze all completed calls that don't have analysis yet"""
    try:
        # Get all completed calls without analysis
        calls = db.query(Call).filter(
            Call.status == "completed"
        ).outerjoin(CallAnalysis).filter(
            CallAnalysis.id == None
        ).all()

        analyzer = CallAnalyzer()
        analyzed_count = 0
        errors = []

        for call in calls:
            try:
                analysis = analyzer.analyze_call(call, db)
                if analysis:
                    analyzed_count += 1
            except Exception as e:
                errors.append(f"Call {call.id}: {str(e)}")

        return JSONResponse({
            "success": True,
            "analyzed_count": analyzed_count,
            "total_calls": len(calls),
            "errors": errors if errors else None
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


# ========================
# Health Check
# ========================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "voice-agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
