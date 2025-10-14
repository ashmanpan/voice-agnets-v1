# LiveKit Voice Agent - Implementation Plan

**Goal:** Build ultra-low latency voice agent (1-3 seconds) using LiveKit

**Current Status:** Code exists but NOT functional yet

---

## 🎯 What We Need to Achieve

Transform the current 15-20 second latency Twilio system into a 1-3 second LiveKit system that:
- Provides real-time conversation
- Handles interruptions
- Maintains all existing features (database, analysis, scheduling)
- Works with phone numbers

---

## 📋 Prerequisites Checklist

### Accounts & Credentials Needed

- [ ] **LiveKit Cloud Account** (https://cloud.livekit.io/)
  - Free tier: 50GB transfer/month
  - Or self-host LiveKit server

- [ ] **Twilio SIP Trunking** (for phone integration)
  - Already have Twilio account ✅
  - Need to set up SIP trunk

- [ ] **API Keys**
  - LiveKit API Key & Secret
  - OpenAI API Key (already have ✅)
  - Groq API Key (already have ✅)

---

## 🏗️ Architecture Overview

### Current Twilio System (v1)
```
Phone → Twilio → Webhook → FastAPI → Groq → TTS → Twilio → Phone
        (2-3s)    (3s)      (2s)      (4s)   (3s)   (2s)
        TOTAL: ~15-20 seconds per response
```

### New LiveKit System (v2)
```
Phone → Twilio SIP → LiveKit Server → Agent Container
                                          ↓
                                    Streaming STT
                                          ↓
                                      Groq AI (streaming)
                                          ↓
                                    Streaming TTS
                                          ↓
                      Real-time audio ← Phone
        TOTAL: ~1-3 seconds per response
```

---

## 📅 Implementation Steps

### STEP 1: Set Up LiveKit Cloud (Day 1)

#### 1.1 Create LiveKit Account
```bash
# Go to: https://cloud.livekit.io/
# Sign up (free tier available)
# Create a new project
```

#### 1.2 Get Credentials
You'll receive:
- `LIVEKIT_URL`: wss://your-project.livekit.cloud
- `LIVEKIT_API_KEY`: APIxxxxxxxx
- `LIVEKIT_API_SECRET`: secretxxxxxxxxx

#### 1.3 Update Environment
```bash
# Add to livekit-agent/.env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Reuse existing keys
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
```

#### 1.4 Test Basic Connection
```bash
# Start LiveKit agent
cd /home/kpanse/wsl-myprojects/voice-agents
docker-compose up livekit-agent

# Should see: "Connected to LiveKit" in logs
docker logs voice-agents-livekit-agent-1 --follow
```

---

### STEP 2: Test Agent with Web Browser (Day 1)

#### 2.1 Use LiveKit Playground
```
1. Go to: https://agents-playground.livekit.io/
2. Enter your LIVEKIT_URL
3. Enter LIVEKIT_API_KEY and API_SECRET
4. Click "Connect"
5. Start speaking to test the agent
```

#### 2.2 What to Verify
- [ ] Agent connects successfully
- [ ] Speech-to-text working
- [ ] AI responses generating
- [ ] Text-to-speech playing
- [ ] Latency < 3 seconds
- [ ] Can interrupt AI mid-sentence

**Expected Result:** Working voice agent in browser with sub-3-second latency

---

### STEP 3: Set Up Twilio SIP Integration (Day 2)

#### 3.1 Create SIP Trunk in Twilio
```
1. Go to: https://console.twilio.com/us1/develop/voice/sip-trunking
2. Click "Create SIP Trunk"
3. Name: "LiveKit Voice Agent"
4. Save the SIP Trunk ID
```

#### 3.2 Configure Origination (Outbound Calls)
```
In Twilio SIP Trunk settings:
1. Origination → Add Origination URI
2. URI: Will be provided by LiveKit
3. Priority: 1
4. Save
```

#### 3.3 Configure Termination (Inbound Calls)
```
In Twilio SIP Trunk settings:
1. Termination → Add Termination URI
2. URI: Will be provided by LiveKit
3. Save
```

#### 3.4 Assign Phone Numbers
```
1. In SIP Trunk → Phone Numbers
2. Add your phone numbers:
   - +17407933007 (US)
   - +61340537198 (AU)
3. Save
```

---

### STEP 4: Connect LiveKit to Twilio (Day 2)

#### 4.1 Configure LiveKit SIP Settings
```bash
# Use LiveKit Cloud Dashboard or API
# Add SIP trunk configuration
```

#### 4.2 Create SIP Dispatch Rules
```python
# In LiveKit, create dispatch rule to route calls to agent
{
  "rule": {
    "roomName": "phone-{callId}",
    "agentName": "voice-assistant"
  }
}
```

#### 4.3 Test Inbound Call
```
1. Call your Twilio number
2. Should connect to LiveKit agent
3. Test conversation
4. Measure latency
```

---

### STEP 5: Update Agent Code (Day 3)

#### 5.1 Current Agent Code Review
```python
# File: livekit-agent/agent.py
# Already has:
- ✅ Agent class structure
- ✅ STT/LLM/TTS pipeline
- ✅ Outbound call support
- ✅ SIP participant creation
```

#### 5.2 Enhancements Needed
```python
# Add database integration
import psycopg2
from datetime import datetime

# Store call metadata
async def store_call_data(room_name, phone_number):
    # Save to PostgreSQL
    pass

# Add transcript logging
async def log_transcript(call_id, speaker, text):
    # Save to transcript_segments table
    pass
```

#### 5.3 Add Custom Greetings
```python
# Support dynamic greetings from database
async def get_greeting(contact_id):
    # Fetch from calls table
    pass
```

---

### STEP 6: Create API Endpoints (Day 3)

#### 6.1 Update main.py
```python
# Add LiveKit call endpoint
@app.post("/api/calls/livekit-call")
async def create_livekit_call(
    name: str = Form(...),
    phone: str = Form(...),
    custom_greeting: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a call using LiveKit instead of Twilio"""

    # 1. Create contact and call record
    # 2. Create LiveKit room
    # 3. Start agent in room
    # 4. Create SIP participant to dial phone
    # 5. Return call details
```

#### 6.2 Make Call Function
```python
from livekit import api

async def make_livekit_call(phone_number, greeting, call_id):
    """
    Make an outbound call using LiveKit
    """
    livekit_api = api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

    # Create room
    room = await livekit_api.room.create_room(
        api.CreateRoomRequest(name=f"call-{call_id}")
    )

    # Dispatch agent
    await livekit_api.agent.create_agent_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="voice-assistant",
            room=room.name,
            metadata=json.dumps({
                "phone_number": phone_number,
                "greeting": greeting,
                "call_id": call_id
            })
        )
    )

    return room
```

---

### STEP 7: Testing & Validation (Day 4)

#### 7.1 Test Scenarios
- [ ] Make outbound call to mobile
- [ ] Receive inbound call
- [ ] Test with multiple contacts
- [ ] Verify database storage
- [ ] Check transcript logging
- [ ] Test custom greetings
- [ ] Measure latency (should be 1-3s)
- [ ] Test interruptions
- [ ] Test with different phone numbers

#### 7.2 Performance Metrics
```python
# Add latency tracking
async def track_latency(event_type, timestamp):
    """Track response times"""
    # STT latency
    # AI processing latency
    # TTS latency
    # Total latency
```

---

### STEP 8: Database Integration (Day 4)

#### 8.1 Update Models
```python
# Add LiveKit-specific fields to Call model
class Call(Base):
    # ... existing fields ...

    # LiveKit integration
    livekit_room_name = Column(String(100))
    livekit_session_id = Column(String(100))
    call_method = Column(String(20))  # 'twilio' or 'livekit'
    avg_latency_ms = Column(Integer)  # Track performance
```

#### 8.2 Run Migration
```bash
docker exec voice-agents-app-1 python migrate_db.py
```

---

### STEP 9: Gradual Migration (Day 5)

#### 9.1 Feature Flag
```python
# Add config to switch between systems
USE_LIVEKIT = os.getenv("USE_LIVEKIT", "false").lower() == "true"

@app.post("/api/calls/facility-test")
async def create_facility_test_call(...):
    if USE_LIVEKIT:
        return await create_livekit_call(...)
    else:
        return await create_twilio_call(...)
```

#### 9.2 A/B Testing
```python
# Route 10% of calls to LiveKit
import random

if random.random() < 0.1:
    use_livekit = True
```

---

### STEP 10: Production Deployment (Day 5)

#### 10.1 Pre-Deployment Checklist
- [ ] All tests passing
- [ ] Latency < 3 seconds consistently
- [ ] Database integration working
- [ ] Error handling robust
- [ ] Monitoring set up
- [ ] Documentation updated

#### 10.2 Deployment Steps
```bash
# 1. Update environment variables
# 2. Restart containers
docker-compose down
docker-compose up -d

# 3. Monitor logs
docker-compose logs -f

# 4. Make test call
curl -X POST http://localhost:8001/api/calls/livekit-call \
  -F "name=Test User" \
  -F "phone=+1234567890"
```

---

## 🔧 Technical Details

### LiveKit Agent Dependencies
```python
# requirements.txt (already configured)
livekit
livekit-agents
livekit-plugins-openai
livekit-plugins-silero
groq
```

### Environment Variables Complete List
```bash
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxx
LIVEKIT_API_SECRET=secretxxx

# Twilio SIP
TWILIO_SIP_TRUNK_ID=TKxxx

# AI Services (existing)
OPENAI_API_KEY=sk-xxx
GROQ_API_KEY=gsk_xxx

# Database (existing)
DATABASE_URL=postgresql://...

# Feature Flags
USE_LIVEKIT=true
LIVEKIT_ENABLED=true
```

---

## 📊 Expected Results

### Before (Twilio v1)
- Latency: 15-20 seconds
- User Experience: Poor (long waits)
- Interruptions: Not supported
- Cost: Higher

### After (LiveKit v2)
- Latency: 1-3 seconds ✨
- User Experience: Excellent (natural conversation)
- Interruptions: Supported ✅
- Cost: Lower at scale

---

## 🚨 Common Issues & Solutions

### Issue 1: Agent Not Connecting
**Symptom:** Agent doesn't join LiveKit room

**Solution:**
```bash
# Check credentials
echo $LIVEKIT_URL
echo $LIVEKIT_API_KEY

# Verify agent is running
docker ps | grep livekit-agent

# Check logs
docker logs voice-agents-livekit-agent-1 --tail 50
```

### Issue 2: No Audio
**Symptom:** Can't hear agent or agent can't hear you

**Solution:**
```bash
# Verify API keys
echo $OPENAI_API_KEY  # For TTS/STT
echo $GROQ_API_KEY    # For LLM

# Check audio codecs in LiveKit dashboard
# Ensure WebRTC ports are open (UDP 50000-60000)
```

### Issue 3: High Latency
**Symptom:** Responses taking > 5 seconds

**Solution:**
```python
# 1. Use faster Groq model
llm="groq/mixtral-8x7b-32768"  # Faster than llama-3.3-70b

# 2. Reduce TTS quality
tts=openai.TTS(speed=1.2)  # Slightly faster

# 3. Check network latency
# Ping LiveKit server
```

### Issue 4: SIP Calls Not Working
**Symptom:** Phone calls don't connect

**Solution:**
```bash
# 1. Verify Twilio SIP trunk is active
# 2. Check phone numbers are assigned to trunk
# 3. Verify LiveKit SIP dispatch rules
# 4. Test with LiveKit SIP simulator first
```

---

## 📚 Resources

### LiveKit Documentation
- Main Docs: https://docs.livekit.io/
- Agents Guide: https://docs.livekit.io/agents/
- SIP Integration: https://docs.livekit.io/sip/
- Python SDK: https://docs.livekit.io/client-sdks/python/

### Twilio SIP Trunking
- Docs: https://www.twilio.com/docs/sip-trunking
- Console: https://console.twilio.com/us1/develop/voice/sip-trunking

### API References
- Groq: https://console.groq.com/docs
- OpenAI: https://platform.openai.com/docs

---

## ✅ Success Criteria

A successful LiveKit implementation means:

1. **Latency:** < 3 seconds average response time
2. **Quality:** Clear audio, no dropouts
3. **Features:** All Twilio features migrated
4. **Database:** Full integration maintained
5. **Scheduler:** Works with LiveKit calls
6. **Analysis:** AI analysis still working
7. **Reports:** Daily reports include LiveKit calls
8. **Reliability:** 99%+ call success rate

---

## 🎯 Next Immediate Actions

**RIGHT NOW:**

1. Create LiveKit Cloud account
2. Get credentials
3. Update `.env` file
4. Start agent container
5. Test in web browser
6. Measure latency

**Commands to run:**
```bash
# 1. Create livekit-agent/.env with credentials
cd /home/kpanse/wsl-myprojects/voice-agents/livekit-agent
cp .env.example .env
# Edit .env with your LiveKit credentials

# 2. Start agent
cd ..
docker-compose up -d livekit-agent

# 3. Watch logs
docker logs voice-agents-livekit-agent-1 --follow

# 4. Test in browser at:
# https://agents-playground.livekit.io/
```

---

**Status:** Ready to begin LiveKit setup! 🚀

**Estimated Time:** 5 days to fully functional system
