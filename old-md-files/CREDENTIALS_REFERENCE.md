# Quick Reference - Credentials & Settings

**Purpose**: All the information you'll need tomorrow in one place

---

## 🔑 LiveKit Cloud

```
URL: wss://voice-agents-aw8yrvjs.livekit.cloud
API Key: APIdmFeUChf7YwF
API Secret: zXhankIHiqBbny11bygr2kt8FdJ3Xnee8gUWp0tzYGU
Region: Singapore
Project ID: voice-agents-aw8yrvjs
Agent Name: voice-assistant
```

**Dashboard**: https://cloud.livekit.io/projects/voice-agents-aw8yrvjs

**Current Status**: ✅ Agent running, connected

---

## 📞 Twilio

```
Phone Number: +16505029399
Account: (check Twilio console)
```

**Console**: https://console.twilio.com

**SIP Trunking**: https://console.twilio.com/us1/develop/sip-trunking

**Phone Numbers**: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming

---

## 🤖 OpenAI

```
API Key: your_openai_api_key_here
```

**Used for**:
- Speech-to-Text (Whisper)
- Text-to-Speech

---

## ⚡ Groq

```
API Key: your_groq_api_key_here
Model: llama-3.3-70b-versatile
```

**Used for**: Ultra-fast LLM inference (~50ms)

---

## 📝 Tomorrow You'll Create

### Twilio SIP Trunk

**Will create**:
- Trunk SID: `TK_____________________________` (save this)
- Termination URI: `__________.pstn.twilio.com` (save this)
- Username: `livekit_user` (or your choice)
- Password: `_______________________________` (generate strong one)

### LiveKit Outbound Trunk

**Will create**:
- Trunk ID: `ST_____________________________` (save this!)
- This is needed to make calls

---

## 🔗 Important Links

### Setup

- **Twilio SIP Trunking**: https://console.twilio.com/us1/develop/sip-trunking
- **Twilio Credentials**: https://console.twilio.com/us1/develop/sip-trunking/credential-lists
- **LiveKit Dashboard**: https://cloud.livekit.io/projects/voice-agents-aw8yrvjs

### Documentation

- **LiveKit SIP Docs**: https://docs.livekit.io/sip/
- **LiveKit Agents Docs**: https://docs.livekit.io/agents/
- **Twilio SIP Trunk Docs**: https://www.twilio.com/docs/sip-trunking

### Monitoring

- **LiveKit Rooms**: https://cloud.livekit.io/projects/voice-agents-aw8yrvjs/rooms
- **Twilio Call Logs**: https://console.twilio.com/us1/monitor/logs/calls
- **OpenAI Usage**: https://platform.openai.com/usage
- **Groq Usage**: https://console.groq.com/usage

---

## 💻 Commands You'll Use

### Check Agent Status

```bash
cd /home/kpanse/wsl-myprojects/voice-agents
docker-compose ps
docker-compose logs -f livekit-agent
```

### Install LiveKit CLI

```bash
curl -sSL https://get.livekit.io/cli | bash
lk --version
lk cloud auth
```

### Create Outbound Trunk

```bash
# Edit config file first with your settings
nano livekit-outbound-trunk.json

# Create trunk
lk sip outbound create livekit-outbound-trunk.json

# List trunks (to verify)
lk sip outbound list
```

### Make Test Call

```bash
cd livekit-agent
python make_call.py +1234567890 ST_xxxxxxxxxxxxx
```

---

## 📋 Trunk Config Template

Save this as `livekit-outbound-trunk.json`:

```json
{
  "trunk": {
    "name": "Twilio Outbound",
    "address": "YOUR_TWILIO_TERMINATION_URI",
    "auth_username": "YOUR_TWILIO_USERNAME",
    "auth_password": "YOUR_TWILIO_PASSWORD",
    "numbers": ["+16505029399"]
  }
}
```

---

## 🎯 Quick Start (Tomorrow)

1. **Verify agent running**: `docker-compose ps`
2. **Create Twilio SIP trunk**: Follow Step 1 in TOMORROW.md
3. **Install LiveKit CLI**: `curl -sSL https://get.livekit.io/cli | bash`
4. **Create LiveKit trunk**: `lk sip outbound create livekit-outbound-trunk.json`
5. **Make test call**: `python make_call.py +PHONE ST_TRUNK_ID`

**Total time**: ~30 minutes

---

## 🚨 Save These After Creation

After completing setup tomorrow, update this section:

```
✅ Twilio SIP Trunk SID: TK_____________________________
✅ Termination SIP URI: __________.pstn.twilio.com
✅ Twilio Username: _______________________________
✅ Twilio Password: _______________________________
✅ LiveKit Trunk ID: ST_____________________________
```

---

## 📊 Expected Performance

| Metric | Old (Webhook) | New (LiveKit) | Improvement |
|--------|---------------|---------------|-------------|
| Latency | 20 seconds | 1-3 seconds | **10x faster** |
| Time to speak | 5-8 seconds | 0.5-1 second | **8x faster** |
| Feel | Robotic | Natural | Much better |

---

## ✅ Current Status

- ✅ Agent code written and tested
- ✅ Docker container built and running
- ✅ Connected to LiveKit Cloud (Singapore)
- ✅ OpenAI Whisper configured for STT
- ✅ Groq LLM configured (ultra-fast)
- ✅ OpenAI TTS configured
- ✅ Outbound call support implemented
- ✅ Call script ready (`make_call.py`)
- ⏳ Twilio SIP trunk (tomorrow)
- ⏳ LiveKit outbound trunk (tomorrow)
- ⏳ End-to-end testing (tomorrow)

---

## 🆘 Emergency Restart

If something's not working:

```bash
# Stop everything
docker-compose down

# Start fresh
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f livekit-agent
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `TOMORROW.md` | ⭐ Step-by-step action plan |
| `PROJECT_STATUS.md` | Complete project overview |
| `OUTBOUND_CALLS_SETUP.md` | Detailed setup guide |
| `CREDENTIALS_REFERENCE.md` | This file - quick reference |
| `livekit-agent/README.md` | Agent documentation |
| `COMPARISON.md` | Twilio vs LiveKit comparison |

---

**Start here tomorrow**: Open `TOMORROW.md` and follow step-by-step! 🚀
