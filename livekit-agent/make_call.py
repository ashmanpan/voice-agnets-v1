#!/usr/bin/env python3
"""
Script to make outbound calls using LiveKit agent

Usage:
    python make_call.py +1234567890 ST_xxxxx

Where:
    +1234567890 is the phone number to call
    ST_xxxxx is your LiveKit SIP trunk ID (get from: lk sip outbound list)
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from livekit import api
import json

load_dotenv()

async def make_call(phone_number: str, sip_trunk_id: str):
    """Make an outbound call using LiveKit"""

    # Get credentials from environment
    livekit_url = os.getenv('LIVEKIT_URL')
    livekit_api_key = os.getenv('LIVEKIT_API_KEY')
    livekit_api_secret = os.getenv('LIVEKIT_API_SECRET')

    if not all([livekit_url, livekit_api_key, livekit_api_secret]):
        print("Error: Missing LiveKit credentials in .env file")
        return

    print(f"Initializing call to {phone_number}...")
    print(f"Using SIP trunk: {sip_trunk_id}")

    # Create LiveKit API client
    livekit_api = api.LiveKitAPI(
        url=livekit_url,
        api_key=livekit_api_key,
        api_secret=livekit_api_secret
    )

    # Create a unique room name for this call
    import time
    room_name = f"call-{int(time.time())}"

    print(f"Creating room: {room_name}")

    try:
        # Create room
        await livekit_api.room.create_room(
            api.CreateRoomRequest(name=room_name)
        )

        # Dispatch agent to the room with phone number metadata
        metadata = json.dumps({
            "phone_number": phone_number,
            "sip_trunk_id": sip_trunk_id
        })

        print(f"Dispatching agent to room...")

        # Note: The agent will automatically join the room based on the dispatch rules
        # and create the SIP participant to make the call

        # Create a dispatch job
        # This requires using the room service to create a room with agent metadata
        await livekit_api.room.update_room_metadata(
            api.UpdateRoomMetadataRequest(
                room=room_name,
                metadata=metadata
            )
        )

        print("✅ Call initiated!")
        print(f"Room: {room_name}")
        print(f"Calling: {phone_number}")
        print(f"\nMonitor the call with: docker-compose logs -f livekit-agent")
        print(f"View in dashboard: https://cloud.livekit.io/projects/voice-agents-aw8yrvjs/rooms/{room_name}")

    except Exception as e:
        print(f"❌ Error initiating call: {e}")
        import traceback
        traceback.print_exc()


def main():
    if len(sys.argv) < 3:
        print("Usage: python make_call.py <phone_number> <sip_trunk_id>")
        print("\nExample:")
        print("  python make_call.py +1234567890 ST_xxxxxxxxxxxxx")
        print("\nTo get your SIP trunk ID, run:")
        print("  lk sip outbound list")
        sys.exit(1)

    phone_number = sys.argv[1]
    sip_trunk_id = sys.argv[2]

    # Validate phone number format
    if not phone_number.startswith('+'):
        print("Error: Phone number must start with + (e.g., +1234567890)")
        sys.exit(1)

    asyncio.run(make_call(phone_number, sip_trunk_id))


if __name__ == "__main__":
    main()
