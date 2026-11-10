"""LiveKit call dispatch — shared by the call/task routers.

Moved out of main.py in Phase 3 so routers can import it without a circular
dependency on the app module.
"""
import os

from sqlalchemy.orm import Session

from models import Call


async def initiate_livekit_call(
    db: Session,
    call_id: int,
    phone_number: str,
    contact_name: str,
    custom_greeting: str = None,
    caller_name: str = None,
    system_prompt: str = None,
    max_turns: int = 8,
    language: str = "en",  # NEW (DROP 8): Language code (en/hi/mr)
):
    """
    Initiate a LiveKit call (1-3 second latency). Default for ALL calls.
    Multi-language support (DROP 8) - English, Hindi, Marathi.
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

        metadata = {
            "phone_number": phone_number,
            "contact_name": contact_name,
            "greeting": custom_greeting,
            "call_id": call_id,
            "caller_name": caller_name or "Krishnaji's CTO office",
            "sip_trunk_id": os.getenv("LIVEKIT_SIP_TRUNK_ID"),
            "system_prompt": system_prompt,
            "max_turns": max_turns,
            "language": language,  # NEW (DROP 8): Pass language to agent
        }

        dispatch_response = await lk_api.agent_dispatch.create_dispatch(
            livekit_api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="voice-assistant",
                metadata=json.dumps(metadata),
            )
        )

        print(f"✅ LiveKit call initiated: Room={room_name}, Phone={phone_number}, Call ID={call_id}")

        call = db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.livekit_room_name = room_name
            call.status = "in-progress"
            db.commit()

        return room_name

    except Exception as e:
        print(f"❌ LiveKit call failed: {e}")
        call = db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.status = "failed"
            db.commit()
        raise
