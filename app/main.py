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

from models import get_db, Contact, Call, TranscriptSegment, CallAnalysis, Task, ActionItem
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

# Security middleware (see app/security.py). add_middleware stacks in reverse,
# so adding RateLimit then APIKey makes auth run first (reject before counting).
from security import APIKeyMiddleware, RateLimitMiddleware  # noqa: E402
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyMiddleware)

# CORS scoped to the frontend origin(s) from CORS_ORIGINS (comma-separated).
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
_cors_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    max_turns: int = 8,
    language: str = "en"  # NEW (DROP 8): Language code (en/hi/mr)
):
    """
    Initiate a LiveKit call (1-3 second latency)
    This is now the default for ALL calls.
    NOW WITH MULTI-LANGUAGE SUPPORT (DROP 8) - English, Hindi, Marathi
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
            "max_turns": max_turns,
            "language": language  # NEW (DROP 8): Pass language to agent
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
    language: str = Form("en"),  # NEW (DROP 8): Language parameter
    db: Session = Depends(get_db)
):
    """Create a personal message call using LiveKit (1-3s latency) with multi-language support"""
    # Create or get contact
    contact = db.query(Contact).filter(Contact.phone_number == phone).first()
    if not contact:
        contact = Contact(
            name=name,
            phone_number=phone,
            contact_type="friend",
            preferred_language=language  # NEW (DROP 8): Set preferred language
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
        language=language,  # NEW (DROP 8): Store language in call record
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
            caller_name=caller_name,
            language=language  # NEW (DROP 8): Pass language to agent
        )
        return JSONResponse({
            "success": True,
            "call_id": call.id,
            "room_name": room_name,
            "message": f"LiveKit call initiated in {language} (1-3s latency!)"
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
    language: str = Form("en"),  # NEW (DROP 8): Language parameter
    db: Session = Depends(get_db)
):
    """Create a facility test call using LiveKit (1-3s latency) with multi-language support"""
    # Create or get contact
    contact = db.query(Contact).filter(Contact.phone_number == phone).first()
    if not contact:
        contact = Contact(
            name=name,
            phone_number=phone,
            contact_type="facility",
            preferred_language=language  # NEW (DROP 8): Set preferred language
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
        custom_subject=custom_subject,
        language=language  # NEW (DROP 8): Store language in call record
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
            caller_name=caller_name,
            language=language  # NEW (DROP 8): Pass language to agent
        )
        return JSONResponse({
            "success": True,
            "call_id": call.id,
            "room_name": room_name,
            "message": f"LiveKit test call initiated in {language} (1-3s latency!)"
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
# Tasks & Actions API
# ========================

@app.post("/api/tasks/assign")
async def assign_task(
    contact_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    task_type: str = Form("reminder"),  # reminder/confirmation/survey/follow_up
    agent_script: str = Form(None),
    questions_to_ask: str = Form(None),  # JSON array
    scheduled_time: str = Form(None),  # ISO datetime
    priority: str = Form("medium"),
    created_by: str = Form("CTO Office"),
    db: Session = Depends(get_db)
):
    """
    Type 1: Assign a proactive task to a contact
    Agent will call the contact to explain the task and collect response
    """
    from models import Task
    try:
        # Validate contact exists
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return JSONResponse({
                "success": False,
                "error": "Contact not found"
            }, status_code=404)

        # Parse scheduled time if provided
        scheduled_datetime = None
        if scheduled_time:
            scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

        # Create task
        task = Task(
            contact_id=contact_id,
            title=title,
            description=description,
            task_type=task_type,
            agent_script=agent_script,
            questions_to_ask=questions_to_ask,
            scheduled_time=scheduled_datetime,
            priority=priority,
            created_by=created_by,
            status="pending"
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # If scheduled, create the call and schedule it
        if scheduled_datetime:
            call = Call(
                contact_id=contact_id,
                call_type="task_delivery",
                status="scheduled",
                caller_name="Krishnaji's CTO office",
                custom_greeting=agent_script or f"Hello, this is a call regarding: {title}",
                is_scheduled=True,
                scheduled_time=scheduled_datetime
            )
            db.add(call)
            db.commit()
            db.refresh(call)

            # Link task to call
            task.assigned_call_id = call.id
            task.status = "scheduled"
            db.commit()

            # Schedule the call
            schedule_one_time_call(call.id, scheduled_datetime)

        return JSONResponse({
            "success": True,
            "task_id": task.id,
            "call_id": task.assigned_call_id if task.assigned_call_id else None,
            "message": f"Task assigned to {contact.name}" +
                      (f" and scheduled for {scheduled_datetime.isoformat()}" if scheduled_datetime else "")
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/tasks")
async def list_tasks(
    status: Optional[str] = None,
    contact_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all proactive tasks (Type 1)
    Filter by status and/or contact
    """
    from models import Task
    try:
        query = db.query(Task).join(Contact)

        if status:
            query = query.filter(Task.status == status)
        if contact_id:
            query = query.filter(Task.contact_id == contact_id)

        tasks = query.order_by(Task.created_at.desc()).limit(limit).all()

        return JSONResponse({
            "success": True,
            "tasks": [
                {
                    "id": task.id,
                    "contact_id": task.contact_id,
                    "contact_name": task.contact.name,
                    "contact_phone": task.contact.phone_number,
                    "title": task.title,
                    "description": task.description,
                    "task_type": task.task_type,
                    "status": task.status,
                    "priority": task.priority,
                    "scheduled_time": task.scheduled_time.isoformat() if task.scheduled_time else None,
                    "created_at": task.created_at.isoformat(),
                    "created_by": task.created_by,
                    "call_attempts": task.call_attempts,
                    "max_attempts": task.max_attempts,
                    "contact_response": task.contact_response,
                    "task_completed": task.task_completed
                }
                for task in tasks
            ],
            "count": len(tasks)
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get specific task details"""
    from models import Task
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return JSONResponse({
                "success": False,
                "error": "Task not found"
            }, status_code=404)

        import json
        return JSONResponse({
            "success": True,
            "task": {
                "id": task.id,
                "contact": {
                    "id": task.contact.id,
                    "name": task.contact.name,
                    "phone": task.contact.phone_number
                },
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type,
                "agent_script": task.agent_script,
                "questions_to_ask": json.loads(task.questions_to_ask) if task.questions_to_ask else [],
                "status": task.status,
                "priority": task.priority,
                "scheduled_time": task.scheduled_time.isoformat() if task.scheduled_time else None,
                "created_at": task.created_at.isoformat(),
                "created_by": task.created_by,
                "call_attempts": task.call_attempts,
                "max_attempts": task.max_attempts,
                "contact_response": task.contact_response,
                "response_sentiment": task.response_sentiment,
                "task_completed": task.task_completed,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "notes": task.notes
            }
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: int,
    status: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update task status or notes"""
    from models import Task
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return JSONResponse({
                "success": False,
                "error": "Task not found"
            }, status_code=404)

        if status:
            task.status = status
            if status == "completed":
                task.completed_at = datetime.utcnow()

        if notes:
            task.notes = notes

        db.commit()

        return JSONResponse({
            "success": True,
            "message": "Task updated successfully"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/tasks/{task_id}/call")
async def initiate_task_delivery_call(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    Initiate a task delivery call immediately
    This properly sets up the call with task_delivery type BEFORE dispatching the agent
    """
    from models import Task
    try:
        # Get the task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return JSONResponse({
                "success": False,
                "error": "Task not found"
            }, status_code=404)

        # Get the contact
        contact = db.query(Contact).filter(Contact.id == task.contact_id).first()
        if not contact:
            return JSONResponse({
                "success": False,
                "error": "Contact not found"
            }, status_code=404)

        # Create call record with task_delivery type FIRST
        # NEW (DROP 8): Use contact's preferred language
        preferred_lang = contact.preferred_language or "en"

        call = Call(
            contact_id=contact.id,
            call_type="task_delivery",  # CRITICAL: Set BEFORE agent starts
            direction="outbound",
            status="queued",
            caller_name="Krishnaji's CTO office",
            language=preferred_lang  # NEW (DROP 8): Set language from contact
        )
        db.add(call)
        db.commit()
        db.refresh(call)

        # Link task to call
        task.assigned_call_id = call.id
        task.status = "in_progress"
        db.commit()

        # Now initiate the call using the helper function
        try:
            room_name = await initiate_livekit_call(
                db=db,
                call_id=call.id,
                phone_number=contact.phone_number,
                contact_name=contact.name,
                custom_greeting=None,  # Agent will generate from task
                caller_name="Krishnaji's CTO office",
                language=preferred_lang  # NEW (DROP 8): Pass language to agent
            )

            return JSONResponse({
                "success": True,
                "task_id": task.id,
                "call_id": call.id,
                "room_name": room_name,
                "message": f"Task delivery call initiated to {contact.name}"
            })

        except Exception as e:
            # Rollback task status if call fails
            task.status = "pending"
            task.assigned_call_id = None
            db.commit()
            raise e

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/actions")
async def list_actions(
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    contact_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all reactive action items (Type 2)
    These are extracted from call conversations
    """
    from models import ActionItem
    try:
        query = db.query(ActionItem).join(Contact)

        if status:
            query = query.filter(ActionItem.status == status)
        if action_type:
            query = query.filter(ActionItem.action_type == action_type)
        if contact_id:
            query = query.filter(ActionItem.contact_id == contact_id)

        actions = query.order_by(
            ActionItem.urgency_score.desc(),
            ActionItem.created_at.desc()
        ).limit(limit).all()

        return JSONResponse({
            "success": True,
            "actions": [
                {
                    "id": action.id,
                    "call_id": action.call_id,
                    "contact_id": action.contact_id,
                    "contact_name": action.contact.name,
                    "contact_phone": action.contact.phone_number,
                    "action_type": action.action_type,
                    "description": action.description,
                    "priority": action.priority,
                    "status": action.status,
                    "urgency_score": action.urgency_score,
                    "assigned_to": action.assigned_to,
                    "created_at": action.created_at.isoformat(),
                    "due_date": action.due_date.isoformat() if action.due_date else None,
                    "source_text": action.source_text
                }
                for action in actions
            ],
            "count": len(actions)
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/actions/{action_id}")
async def get_action(action_id: int, db: Session = Depends(get_db)):
    """Get specific action item details"""
    from models import ActionItem
    try:
        action = db.query(ActionItem).filter(ActionItem.id == action_id).first()
        if not action:
            return JSONResponse({
                "success": False,
                "error": "Action not found"
            }, status_code=404)

        return JSONResponse({
            "success": True,
            "action": {
                "id": action.id,
                "call_id": action.call_id,
                "contact": {
                    "id": action.contact.id,
                    "name": action.contact.name,
                    "phone": action.contact.phone_number
                },
                "action_type": action.action_type,
                "description": action.description,
                "priority": action.priority,
                "status": action.status,
                "urgency_score": action.urgency_score,
                "assigned_to": action.assigned_to,
                "created_at": action.created_at.isoformat(),
                "due_date": action.due_date.isoformat() if action.due_date else None,
                "completed_at": action.completed_at.isoformat() if action.completed_at else None,
                "notes": action.notes,
                "source_text": action.source_text
            }
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.patch("/api/actions/{action_id}")
async def update_action(
    action_id: int,
    status: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    assigned_to: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update action item status, notes, or assignment"""
    from models import ActionItem
    try:
        action = db.query(ActionItem).filter(ActionItem.id == action_id).first()
        if not action:
            return JSONResponse({
                "success": False,
                "error": "Action not found"
            }, status_code=404)

        if status:
            action.status = status
            if status == "completed":
                action.completed_at = datetime.utcnow()

        if notes:
            action.notes = notes

        if assigned_to:
            action.assigned_to = assigned_to

        db.commit()

        return JSONResponse({
            "success": True,
            "message": "Action updated successfully"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


# ========================
# LiveKit Webhooks
# ========================

@app.post("/livekit/webhook")
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
