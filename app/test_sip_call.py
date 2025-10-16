#!/usr/bin/env python3
"""
Test SIP call with detailed error output
"""
import asyncio
import os
from dotenv import load_dotenv
from livekit.api import LiveKitAPI
from livekit import api as livekit_api

load_dotenv()

async def test_sip_call():
    """Test creating a SIP participant with detailed error logging"""

    lk_api = LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    print("=" * 80)
    print("Testing LiveKit SIP Call")
    print("=" * 80)
    print(f"LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    print(f"API Key: {os.getenv('LIVEKIT_API_KEY')}")
    print(f"Trunk ID: {os.getenv('LIVEKIT_SIP_TRUNK_ID')}")
    print()

    # First, create a room
    room_name = "test-call-001"
    try:
        print(f"Creating room: {room_name}")
        room = await lk_api.room.create_room(
            livekit_api.CreateRoomRequest(name=room_name)
        )
        print(f"✅ Room created: {room.name}")
    except Exception as e:
        print(f"❌ Failed to create room: {e}")
        return

    # Now try to create SIP participant
    trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")
    phone = "+6583188198"

    print()
    print(f"Creating SIP participant:")
    print(f"  Room: {room_name}")
    print(f"  Trunk ID: {trunk_id}")
    print(f"  Phone: {phone}")

    try:
        sip_participant = await lk_api.sip.create_sip_participant(
            livekit_api.CreateSIPParticipantRequest(
                room_name=room_name,
                sip_trunk_id=trunk_id,
                sip_call_to=phone,
                participant_identity=f"phone-{phone}",
                participant_name="Test User"
            )
        )
        print(f"✅ SIP participant created!")
        print(f"   Participant ID: {sip_participant.participant_id}")
        print(f"   SIP Call ID: {sip_participant.sip_call_id}")

    except Exception as e:
        print(f"❌ Failed to create SIP participant:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error: {e}")

        # Try to get more details
        if hasattr(e, 'args'):
            print(f"   Args: {e.args}")
        if hasattr(e, '__dict__'):
            print(f"   Details: {e.__dict__}")

    print()
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_sip_call())
