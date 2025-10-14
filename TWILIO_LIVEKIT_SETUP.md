# Twilio + LiveKit Integration Guide

## Complete setup to receive phone calls via Twilio and handle them with your LiveKit agent

---

## Step 1: Configure LiveKit SIP (in LiveKit Cloud Dashboard)

### 1.1 Access SIP Settings
Go to: https://cloud.livekit.io/projects/voice-agents-aw8yrvjs/settings/sip

### 1.2 Create Inbound SIP Trunk
1. Click **"Create Inbound Trunk"**
2. Configure:
   - **Name**: `Twilio Trunk`
   - **Auth Username**: Choose a username (e.g., `twilio_user`)
   - **Auth Password**: Generate a strong password
3. **Save** the trunk
4. **Copy the SIP URI** - it will look like: `sip:xxx@sip.livekit.cloud`

### 1.3 Create Dispatch Rule
1. Go to **"Dispatch Rules"** tab
2. Click **"Create Dispatch Rule"**
3. Configure:
   - **Rule Type**: Individual (one room per call)
   - **Room Prefix**: `call-`
   - **Agent Name**: `voice-assistant` (must match the agent_name in our code)
4. **Save** the dispatch rule

---

## Step 2: Configure Twilio to Forward Calls to LiveKit

### 2.1 Create TwiML Bin
1. Go to: https://console.twilio.com/us1/develop/twiml-bins/twiml-bins
2. Click **"Create new TwiML Bin"**
3. **Friendly Name**: `LiveKit SIP Forward`
4. **TwiML**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Sip username="YOUR_SIP_USERNAME" password="YOUR_SIP_PASSWORD">
      sip:YOUR_PHONE_NUMBER@sip.livekit.cloud
    </Sip>
  </Dial>
</Response>
```

**Replace**:
- `YOUR_SIP_USERNAME` - The username you created in Step 1.2
- `YOUR_SIP_PASSWORD` - The password you created in Step 1.2
- `YOUR_PHONE_NUMBER` - Your Twilio phone number (e.g., +16505551234)
- `sip.livekit.cloud` - Your LiveKit SIP endpoint from Step 1.2

5. **Save** the TwiML Bin

### 2.2 Configure Your Twilio Phone Number
1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click on your phone number
3. Under **"Voice Configuration"**:
   - **A call comes in**: Select "TwiML Bin"
   - Choose the TwiML Bin you just created
4. **Save**

---

## Step 3: Test the Integration

### 3.1 Verify Agent is Running
```bash
docker-compose logs -f livekit-agent
```

You should see:
```
{"message": "registered worker", "agent_name": "voice-assistant", ...}
```

### 3.2 Make a Test Call
1. Call your Twilio phone number from any phone
2. You should hear: "Hello! This is an AI assistant calling from Krishnaji's CTO office. May I speak with you for a moment?"
3. Start talking - the AI will respond!

### 3.3 Monitor the Call
Watch the agent logs to see:
- Room connection
- Speech transcription
- AI responses
- TTS synthesis

```bash
docker-compose logs -f livekit-agent
```

---

## Architecture Flow

```
Phone Call
    ↓
Twilio Phone Number
    ↓
TwiML Bin (forwards via SIP)
    ↓
LiveKit SIP Inbound Trunk
    ↓
LiveKit Dispatch Rule (routes to room)
    ↓
LiveKit Room (call-XXXXX)
    ↓
Voice Assistant Agent (joins room)
    ↓
Real-time conversation (STT → LLM → TTS)
```

---

## Expected Latency

- **Twilio webhook approach**: 13-22 seconds per turn
- **Twilio + LiveKit SIP**: **1-3 seconds per turn** ⚡

---

## Troubleshooting

### Issue: Call connects but no audio
- Check that SIP credentials in TwiML match the LiveKit trunk
- Verify the SIP URI is correct

### Issue: Agent doesn't join the room
- Verify dispatch rule has agent_name: `voice-assistant`
- Check agent logs for connection errors
- Restart agent: `docker-compose restart livekit-agent`

### Issue: Call drops immediately
- Check TwiML syntax is correct
- Verify LiveKit SIP trunk is enabled
- Check LiveKit Cloud logs

---

## What You Have Now

- ✅ LiveKit agent running with agent_name: `voice-assistant`
- ✅ OpenAI Whisper for STT
- ✅ Groq LLM (llama-3.3-70b-versatile) for fast responses
- ✅ OpenAI TTS for speech synthesis
- ⏳ SIP integration (you need to configure in LiveKit Cloud)
- ⏳ Twilio TwiML (you need to create and configure)

---

## Next Steps

1. Complete **Step 1**: Set up SIP in LiveKit Cloud
2. Complete **Step 2**: Configure Twilio TwiML
3. **Test** by calling your Twilio number
4. **Compare** latency with the old webhook approach
5. **Celebrate** the 10x latency improvement! 🎉
