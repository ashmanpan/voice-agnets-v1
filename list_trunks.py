#!/usr/bin/env python3
"""
List LiveKit SIP trunks
"""
import os
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

token = create_api_token()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("Listing LiveKit SIP Trunks")
print("=" * 80)
print()

# List outbound trunks
print("📋 Outbound Trunks:")
try:
    response = requests.post(
        f"{api_url}/sip/ListSIPOutboundTrunk",
        headers=headers,
        json={},
        timeout=10
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200 and response.text.strip() and response.text != "OK":
        result = response.json()
        if 'items' in result and result['items']:
            for trunk in result['items']:
                print(f"  ✓ {trunk.get('name')}")
                print(f"    ID: {trunk.get('sip_trunk_id') or trunk.get('sipTrunkId')}")
                print(f"    Address: {trunk.get('address')}")
                print(f"    Numbers: {trunk.get('numbers')}")
                print()
        else:
            print("  (no trunks found)")
    else:
        print("  (unable to parse response)")

except Exception as e:
    print(f"  Error: {e}")

print()

# List inbound trunks
print("📋 Inbound Trunks:")
try:
    response = requests.post(
        f"{api_url}/sip/ListSIPInboundTrunk",
        headers=headers,
        json={},
        timeout=10
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")

    if response.status_code == 200 and response.text.strip() and response.text != "OK":
        result = response.json()
        if 'items' in result and result['items']:
            for trunk in result['items']:
                print(f"  ✓ {trunk.get('name')}")
                print(f"    ID: {trunk.get('sip_trunk_id') or trunk.get('sipTrunkId')}")
                print(f"    Numbers: {trunk.get('numbers')}")
                print()
        else:
            print("  (no trunks found)")
    else:
        print("  (unable to parse response or no trunks)")

except Exception as e:
    print(f"  Error: {e}")
