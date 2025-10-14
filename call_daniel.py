#!/usr/bin/env python3
"""
Quick script to call Daniel Clark
"""
import requests

# Your API endpoint
API_URL = "http://localhost:8001/api/calls/facility-test"

# Contact details
name = "Daniel Clark"
phone = "+61421856756"

print(f"Initiating call to {name} at {phone}...")

try:
    response = requests.post(
        API_URL,
        data={
            "name": name,
            "phone": phone
        }
    )

    result = response.json()

    if result.get("success"):
        print(f"✅ Call initiated successfully!")
        print(f"   Call ID: {result.get('call_id')}")
        print(f"   Twilio SID: {result.get('call_sid')}")
        print(f"\n📞 Daniel Clark's phone should be ringing now...")
    else:
        print(f"❌ Call failed: {result.get('error')}")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure your app is running on port 8001:")
    print("  docker-compose ps")
