#!/usr/bin/env python3
"""
Quick script to make a LiveKit call
Usage: python quick_call.py +1234567890 "John Doe"
"""
import asyncio
import sys
import os
from dotenv import load_dotenv
from livekit import api
import json

# Load from livekit-agent/.env
load_dotenv('livekit-agent/.env')

async def make_call(phone_number: str, contact_name: str = "there"):
    """Make an outbound call using LiveKit"""

    # Get credentials
    livekit_url = os.getenv('LIVEKIT_URL')
    livekit_api_key = os.getenv('LIVEKIT_API_KEY')
    livekit_api_secret = os.getenv('LIVEKIT_API_SECRET')
    sip_trunk_id = os.getenv('SIP_OUTBOUND_TRUNK_ID')

    if not all([livekit_url, livekit_api_key, livekit_api_secret, sip_trunk_id]):
        print("❌ Error: Missing credentials in livekit-agent/.env")
        return

    print(f"📞 Initiating call to {phone_number} (Contact: {contact_name})")
    print(f"🔧 SIP Trunk: {sip_trunk_id}")

    # Create LiveKit API client
    lk_api = api.LiveKitAPI(
        url=livekit_url,
        api_key=livekit_api_key,
        api_secret=livekit_api_secret
    )

    # Create unique room name
    import time
    room_name = f"call-{int(time.time())}"

    print(f"🏠 Creating room: {room_name}")

    try:
        # Prepare metadata for agent
        metadata = {
            "phone_number": phone_number,
            "contact_name": contact_name,
            "sip_trunk_id": sip_trunk_id,
            "caller_name": "Krishnaji's CTO office"
        }

        # Dispatch agent to new room
        dispatch_response = await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="voice-assistant",
                metadata=json.dumps(metadata)
            )
        )

        print(f"\n✅ Call initiated successfully!")
        print(f"   Room: {room_name}")
        print(f"   Dispatch ID: {dispatch_response.id}")
        print(f"   Calling: {phone_number}")
        print(f"\n📊 Monitor: https://cloud.livekit.io/projects/voice-agents-aw8yrvjs/rooms/{room_name}")
        print(f"📋 Logs: docker.exe logs -f voice-agents-livekit-agent-1")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_call.py <phone_number> [contact_name]")
        print("\nExamples:")
        print("  python quick_call.py +1234567890")
        print("  python quick_call.py +61411314178 'Senthil'")
        sys.exit(1)

    phone = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "there"

    if not phone.startswith('+'):
        print("❌ Error: Phone number must start with + (e.g., +1234567890)")
        sys.exit(1)

    asyncio.run(make_call(phone, name))
