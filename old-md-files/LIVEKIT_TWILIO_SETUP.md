# LiveKit + Twilio SIP Integration Guide

## Goal
Make phone calls through LiveKit agent with 1-3 second latency (vs 15-20 seconds with current Twilio webhook system)

---

## 🏗️ Architecture

```
Phone Number → Twilio SIP Trunk → LiveKit SIP → LiveKit Agent (Docker)
                                                        ↓
                                                  Streaming STT
                                                        ↓
                                                    Groq AI
                                                        ↓
                                                  Streaming TTS
                                                        ↓
                                              Real-time Audio → Phone
```

---

## 📋 Step-by-Step Setup

### **STEP 1: Create Twilio SIP Trunk**

1. Go to: https://console.twilio.com/us1/develop/voice/sip-trunking/trunks
2. Click **"Create SIP Trunk"**
3. **Name:** "LiveKit Voice Agent"
4. Click **Create**
5. **Copy the SIP Trunk ID** (starts with `TK...`)

---

### **STEP 2: Configure LiveKit SIP**

LiveKit Cloud needs to be configured to accept SIP calls. There are two options:

#### **Option A: LiveKit Cloud SIP (Recommended)**

LiveKit Cloud has built-in SIP support. You need to:

1. Go to your LiveKit Cloud dashboard
2. Navigate to **SIP Settings** (or **Integrations**)
3. Enable SIP
4. Get your **LiveKit SIP URI** (format: `sip:xxx@sip.livekit.cloud`)

#### **Option B: Self-Hosted LiveKit SIP**

If using self-hosted LiveKit, you need to run the LiveKit SIP service:

```bash
docker run -d --name livekit-sip \
  -e LIVEKIT_URL=wss://voice-agents-aw8yrvjs.livekit.cloud \
  -e LIVEKIT_API_KEY=APIdmFeUChf7YwF \
  -e LIVEKIT_API_SECRET=zXhankIHiqBbny11bygr2kt8FdJ3Xnee8gUWp0tzYGU \
  livekit/sip:latest
```

---

### **STEP 3: Connect Twilio to LiveKit**

#### **3.1 Configure Origination (Outbound Calls)**

In your Twilio SIP Trunk:

1. Click **Origination**
2. Click **Add New Origination URI**
3. **URI:** `sip:YOUR_LIVEKIT_SIP_ENDPOINT`
   - Example: `sip:sip.livekit.cloud`
4. **Priority:** 1
5. **Weight:** 10
6. **Enabled:** ✅
7. Click **Save**

#### **3.2 Configure Termination (Inbound Calls)**

In your Twilio SIP Trunk:

1. Click **Termination**
2. **Termination SIP URI:** Will be provided by LiveKit
3. Click **Add**
4. Add LiveKit's IP addresses to whitelist (if required)

#### **3.3 Assign Phone Numbers**

1. In SIP Trunk → **Phone Numbers**
2. Click **Assign a Phone Number**
3. Select your numbers:
   - +17407933007 (US)
   - +61340537198 (AU)
4. Click **Assign**

---

### **STEP 4: Create LiveKit SIP Dispatch Rules**

Dispatch rules tell LiveKit which agent to use for incoming calls.

Create a file: `livekit-sip-config.json`

```json
{
  "rules": [
    {
      "rule_id": "voice-agent-rule",
      "trunk_ids": ["YOUR_TWILIO_TRUNK_ID"],
      "dispatch_rule": {
        "room_name": "phone-call-{call_id}",
        "agent_name": "voice-assistant"
      }
    }
  ]
}
```

Apply the rules using LiveKit CLI or API:

```bash
livekit-cli sip dispatch create \
  --api-key APIdmFeUChf7YwF \
  --api-secret zXhankIHiqBbny11bygr2kt8FdJ3Xnee8gUWp0tzYGU \
  --url wss://voice-agents-aw8yrvjs.livekit.cloud \
  --config livekit-sip-config.json
```

---

### **STEP 5: Update Agent Code for Phone Calls**

The agent code (`livekit-agent/agent.py`) already supports phone calls via SIP. It's configured to:

1. Accept incoming SIP calls
2. Create SIP participants for outbound calls
3. Use the agent name "voice-assistant" (matches dispatch rule)

**Key sections in agent.py:**
```python
# Handles outbound calls
if phone_number and sip_trunk_id:
    await ctx.api.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            room_name=ctx.room.name,
            sip_trunk_id=sip_trunk_id,
            sip_call_to=phone_number,
            participant_identity=phone_number,
        )
    )
```

---

### **STEP 6: Create API Endpoint for LiveKit Calls**

Add to `app/main.py`:

```python
from livekit import api as livekit_api
import json

@app.post("/api/calls/livekit-call")
async def create_livekit_call(
    name: str = Form(...),
    phone: str = Form(...),
    custom_greeting: str = Form(None),
    db: Session = Depends(get_db)
):
    """Make a call using LiveKit (1-3 second latency)"""

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
    call = Call(
        contact_id=contact.id,
        call_type="facility_test",
        status="queued",
        custom_greeting=custom_greeting or "Hello! This is an AI assistant calling from Krishnaji's CTO office.",
        call_method="livekit"  # Track that this uses LiveKit
    )
    db.add(call)
    db.commit()
    db.refresh(call)

    # 3. Create LiveKit room
    lk_api = livekit_api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    room_name = f"call-{call.id}"

    try:
        # Create room
        room = await lk_api.room.create_room(
            livekit_api.CreateRoomRequest(name=room_name)
        )

        # Create agent dispatch with metadata
        metadata = {
            "phone_number": phone,
            "greeting": custom_greeting or "Hello! This is an AI assistant.",
            "call_id": call.id,
            "sip_trunk_id": os.getenv("TWILIO_SIP_TRUNK_ID")
        }

        await lk_api.agent.create_agent_dispatch(
            livekit_api.CreateAgentDispatchRequest(
                agent_name="voice-assistant",
                room=room_name,
                metadata=json.dumps(metadata)
            )
        )

        # Update call record
        call.livekit_room_name = room_name
        call.status = "in-progress"
        db.commit()

        return JSONResponse({
            "success": True,
            "call_id": call.id,
            "room_name": room_name,
            "message": "LiveKit call initiated"
        })

    except Exception as e:
        call.status = "failed"
        db.commit()
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
```

---

### **STEP 7: Update Environment Variables**

Add to `.env`:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://voice-agents-aw8yrvjs.livekit.cloud
LIVEKIT_API_KEY=APIdmFeUChf7YwF
LIVEKIT_API_SECRET=zXhankIHiqBbny11bygr2kt8FdJ3Xnee8gUWp0tzYGU

# Twilio SIP Trunk
TWILIO_SIP_TRUNK_ID=TKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### **STEP 8: Test with Stored Contacts**

Make calls to your stored contacts:

```bash
# Call Daniel Clark via LiveKit
curl -X POST http://localhost:8001/api/calls/livekit-call \
  -F "name=Daniel Clark" \
  -F "phone=+61421856756" \
  -F "custom_greeting=Hello Daniel! This is a LiveKit test call from Krishnaji's CTO office."

# Call Senthil via LiveKit
curl -X POST http://localhost:8001/api/calls/livekit-call \
  -F "name=Senthil" \
  -F "phone=+61411314178"

# Call Rohit via LiveKit
curl -X POST http://localhost:8001/api/calls/livekit-call \
  -F "name=Rohit" \
  -F "phone=+6585221630"
```

---

## 📊 Latency Comparison Testing

### Test Script

Create `test_latency_comparison.py`:

```python
import requests
import time
from datetime import datetime

contacts = [
    {"name": "Daniel Clark", "phone": "+61421856756"},
    {"name": "Senthil", "phone": "+61411314178"},
    {"name": "Rohit", "phone": "+6585221630"},
    {"name": "Kabeer", "phone": "+61455906866"},
]

results = {
    "twilio": [],
    "livekit": []
}

print("Starting Latency Comparison Test")
print("=" * 60)

for contact in contacts:
    print(f"\nTesting {contact['name']} ({contact['phone']})")

    # Test Twilio (old system)
    print("  - Twilio call...")
    start = time.time()
    response = requests.post(
        "http://localhost:8001/api/calls/facility-test",
        data=contact
    )
    twilio_time = time.time() - start
    results["twilio"].append({
        "contact": contact["name"],
        "init_time": twilio_time,
        "call_id": response.json().get("call_id")
    })
    print(f"    Init time: {twilio_time:.2f}s")

    time.sleep(5)  # Wait between calls

    # Test LiveKit (new system)
    print("  - LiveKit call...")
    start = time.time()
    response = requests.post(
        "http://localhost:8001/api/calls/livekit-call",
        data=contact
    )
    livekit_time = time.time() - start
    results["livekit"].append({
        "contact": contact["name"],
        "init_time": livekit_time,
        "call_id": response.json().get("call_id")
    })
    print(f"    Init time: {livekit_time:.2f}s")

    time.sleep(5)  # Wait between calls

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

avg_twilio = sum(r["init_time"] for r in results["twilio"]) / len(results["twilio"])
avg_livekit = sum(r["init_time"] for r in results["livekit"]) / len(results["livekit"])

print(f"\nAverage Twilio Init Time:  {avg_twilio:.2f}s")
print(f"Average LiveKit Init Time: {avg_livekit:.2f}s")
print(f"Improvement: {((avg_twilio - avg_livekit) / avg_twilio * 100):.1f}% faster")
```

Run:
```bash
python test_latency_comparison.py
```

---

## ✅ Expected Results

### **Twilio System (v1)**
- **Call Initiation:** 2-3 seconds
- **First Response:** 15-20 seconds
- **Subsequent Responses:** 15-20 seconds each
- **Total Conversation Time:** Very slow

### **LiveKit System (v2)**
- **Call Initiation:** 1-2 seconds
- **First Response:** 1-3 seconds ⚡
- **Subsequent Responses:** 1-3 seconds each ⚡
- **Total Conversation Time:** Near real-time

### **Improvement: ~85% faster response times!**

---

## 🔧 Troubleshooting

### Issue: "SIP Trunk not found"
- Verify `TWILIO_SIP_TRUNK_ID` is correct
- Check SIP trunk is active in Twilio console

### Issue: "Agent not connecting"
- Verify LiveKit agent is running: `docker ps | grep livekit`
- Check agent logs: `docker logs voice-agents-livekit-agent-1`
- Ensure dispatch rules are configured

### Issue: "No audio"
- Check OpenAI API key for TTS/STT
- Verify Groq API key for LLM
- Test in LiveKit playground first

### Issue: "High latency still"
- Use faster Groq model: `mixtral-8x7b-32768`
- Check network connectivity
- Verify WebRTC ports are open

---

## 📚 Resources

- **Twilio SIP Trunking:** https://console.twilio.com/us1/develop/voice/sip-trunking
- **LiveKit Dashboard:** https://cloud.livekit.io/
- **LiveKit Docs:** https://docs.livekit.io/
- **Current Status:** See CURRENT_STATUS.md

---

**Next Step:** Create the Twilio SIP Trunk and get the Trunk ID!
