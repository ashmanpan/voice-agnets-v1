#!/usr/bin/env python3
"""
Simple script to create LiveKit SIP trunk using HTTP API
"""
import os
import sys
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Convert WebSocket URL to HTTP API URL
api_url = LIVEKIT_URL.replace("wss://", "https://").replace("ws://", "http://")

# Create authorization header
auth = f"{LIVEKIT_API_KEY}:{LIVEKIT_API_SECRET}"
auth_encoded = base64.b64encode(auth.encode()).decode()

headers = {
    "Authorization": f"Bearer {auth_encoded}",
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

print("Creating outbound SIP trunk...")
print(f"API URL: {api_url}/sip/CreateSIPOutboundTrunk")
print(f"Trunk data: {trunk_data}")
print()

try:
    response = requests.post(
        f"{api_url}/sip/CreateSIPOutboundTrunk",
        headers=headers,
        json=trunk_data,
        timeout=10
    )

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")

    if response.status_code == 200:
        result = response.json()
        print("\n✅ Outbound trunk created successfully!")
        print(f"Trunk ID: {result.get('sip_trunk_id')}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
