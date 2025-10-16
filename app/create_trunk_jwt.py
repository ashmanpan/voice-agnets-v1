#!/usr/bin/env python3
"""
Create LiveKit SIP trunk using proper JWT authentication
"""
import os
import sys
import requests
import jwt
import time
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Convert WebSocket URL to HTTP API URL
api_url = LIVEKIT_URL.replace("wss://", "https://").replace("ws://", "http://")

# Create JWT token for authentication
def create_api_token():
    """Create a JWT token for LiveKit API access"""
    now = int(time.time())

    payload = {
        "iss": LIVEKIT_API_KEY,
        "sub": LIVEKIT_API_KEY,
        "iat": now,
        "exp": now + 3600,  # 1 hour expiry
        "video": {
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True
        }
    }

    token = jwt.encode(payload, LIVEKIT_API_SECRET, algorithm="HS256")
    return token

# Create authorization token
token = create_api_token()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Create outbound trunk
trunk_data = {
    "trunk": {
        "name": "Twilio Outbound Trunk",
        "address": "sip.twilio.com",
        "numbers": ["+61340537198", "+17407933007"]
    }
}

print("=" * 80)
print("Creating LiveKit Outbound SIP Trunk")
print("=" * 80)
print(f"API URL: {api_url}/sip/CreateSIPOutboundTrunk")
print(f"API Key: {LIVEKIT_API_KEY}")
print(f"Trunk Name: Twilio Outbound Trunk")
print(f"Numbers: +61340537198, +17407933007")
print()

try:
    response = requests.post(
        f"{api_url}/sip/CreateSIPOutboundTrunk",
        headers=headers,
        json=trunk_data,
        timeout=10
    )

    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    print()

    if response.status_code == 200:
        result = response.json()
        trunk_id = result.get('sip_trunk_id') or result.get('sipTrunkId')
        print("=" * 80)
        print("✅ SUCCESS! Outbound trunk created")
        print("=" * 80)
        print(f"Trunk ID: {trunk_id}")
        print()
        print("Next steps:")
        print(f"1. Update .env with: LIVEKIT_SIP_TRUNK_ID={trunk_id}")
        print("2. Test the call!")
    elif response.status_code == 401:
        print("❌ Authentication failed")
        print("Check your LIVEKIT_API_KEY and LIVEKIT_API_SECRET")
    elif response.status_code == 403:
        print("❌ Permission denied")
        print("Your LiveKit account may not have SIP/telephony features enabled")
        print("Contact LiveKit support to enable telephony on your account")
    else:
        print(f"❌ Error: {response.status_code}")

except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
