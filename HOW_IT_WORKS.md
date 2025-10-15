# How the Voice Agent System Works

## System Overview

The voice agent system consists of 3 Docker containers working together:

1. **PostgreSQL Database** (`voice-agents-db-1`) - Stores contacts, calls, transcripts
2. **FastAPI Server** (`voice-agents-app-1`) - Web dashboard and API endpoints
3. **LiveKit Agent** (`voice-agents-livekit-agent-1`) - Real-time voice agent with 1-3s latency

## Architecture

```
User → FastAPI Server (port 8001) → LiveKit Cloud → Phone Call
          ↓                            ↓
      Database ←───────────────── LiveKit Agent
```

## How Calls Work (End-to-End)

### 1. Call Initiation
When you make a call via the API:
```bash
curl -X POST http://localhost:8001/api/calls/facility-test \
  -F "name=John Doe" \
  -F "phone=+1234567890" \
  -F "custom_greeting=Hi, this is a test call"
```

### 2. What Happens:

**Step 1: FastAPI Server** (`app/main.py:207`)
- Creates/finds contact in database
- Creates call record with status "queued"
- Calls `initiate_livekit_call()` function

**Step 2: LiveKit API Call** (`app/main.py:43-108`)
- Creates LiveKitAPI client using credentials from `.env`
- Generates room name: `call-{call_id}`
- Prepares metadata with:
  - phone_number
  - contact_name
  - greeting
  - sip_trunk_id (for making the actual phone call)
- **Dispatches agent** using `lk_api.agent_dispatch.create_dispatch()`
  - This tells LiveKit Cloud to start an agent
  - Agent name: "voice-assistant"
  - Passes metadata to agent

**Step 3: LiveKit Agent Receives Dispatch** (`livekit-agent/agent.py`)
- Agent running in `voice-agents-livekit-agent-1` container
- Receives dispatch from LiveKit Cloud
- Joins the room specified in dispatch
- Reads metadata to get phone number and greeting

**Step 4: Agent Makes Phone Call**
- Agent uses LiveKit's SIP integration
- Creates outbound SIP participant using the phone number
- Connects to Twilio SIP trunk (`ST_RhrrdV53c5Ww`)
- Twilio makes the actual phone call

**Step 5: Conversation**
- When person answers, agent says the greeting
- Uses OpenAI Realtime API for natural conversation
- Ultra-low latency: 1-3 seconds total!
- Transcripts saved to database

**Step 6: Call Ends**
- LiveKit sends webhook to `/livekit/webhook`
- Database updated with call status "completed"
- Background thread analyzes call and extracts insights

## Critical Components

### Requirements (app container)
The app container MUST have these LiveKit packages:
```
livekit>=0.17.0
livekit-api>=1.0.0
```

**Why it broke before:**
- Old version (livekit-api 0.5.0) doesn't have `agent_dispatch` attribute
- Build cache kept old version even after requirements.txt update
- Solution: Rebuilt container with `docker compose down app && docker compose up -d app`

### Environment Variables

**App Container** (`app/.env` or docker-compose.yml):
```
LIVEKIT_URL=wss://voice-agents-aw8yrvjs.livekit.cloud
LIVEKIT_API_KEY=APIdmFeUChf7YwF
LIVEKIT_API_SECRET=zXhankIHiqBbny11bygr2kt8FdJ3Xnee8gUWp0tzYGU
LIVEKIT_SIP_TRUNK_ID=ST_RhrrdV53c5Ww
```

**LiveKit Agent** (`livekit-agent/.env`):
```
LIVEKIT_URL=wss://voice-agents-aw8yrvjs.livekit.cloud
LIVEKIT_API_KEY=APIdmFeUChf7YwF
LIVEKIT_API_SECRET=zXhankIHiqBbny11bygr2kt8FdJ3Xnee8gUWp0tzYGU
SIP_OUTBOUND_TRUNK_ID=ST_RhrrdV53c5Ww
OPENAI_API_KEY=<your-key>
```

## How to Make a Call

### Method 1: Web Dashboard
1. Open http://localhost:8001
2. Fill in contact details
3. Click "Make Call"

### Method 2: API (Recommended)
```bash
curl -X POST http://localhost:8001/api/calls/facility-test \
  -F "name=John Doe" \
  -F "phone=+1234567890" \
  -F "custom_greeting=Hi John, this is a test call"
```

### Method 3: Scheduled Calls
```bash
curl -X POST http://localhost:8001/api/calls/schedule \
  -F "name=John Doe" \
  -F "phone=+1234567890" \
  -F "call_type=facility_test" \
  -F "scheduled_time=2025-10-15T10:00:00Z"
```

### Method 4: Recurring Calls
```bash
curl -X POST http://localhost:8001/api/calls/recurring \
  -F "name=John Doe" \
  -F "phone=+1234567890" \
  -F "call_type=facility_test" \
  -F "recurrence_pattern=daily" \
  -F "recurrence_time=09:00"
```

## Monitoring Calls

### Check Call Status in Database
```bash
docker exec voice-agents-db-1 psql -U voiceagent -d voiceagent \
  -c "SELECT id, call_type, status, livekit_room_name, created_at FROM calls ORDER BY created_at DESC LIMIT 5;"
```

### Watch LiveKit Agent Logs
```bash
docker logs -f voice-agents-livekit-agent-1
```

### Watch API Server Logs
```bash
docker logs -f voice-agents-app-1
```

### LiveKit Cloud Dashboard
https://cloud.livekit.io/projects/voice-agents-aw8yrvjs/rooms/{room_name}

## Troubleshooting

### Call Not Received

**Check 1: Container Status**
```bash
docker ps --filter "name=voice-agents"
```
All 3 containers should be "Up"

**Check 2: LiveKit Agent Running**
```bash
docker logs voice-agents-livekit-agent-1 | tail -20
```
Should see "registered worker" message

**Check 3: Phone Number Format**
Must start with `+` and include country code:
- ✅ `+919820754198` (India)
- ✅ `+12025551234` (USA)
- ❌ `9820754198` (missing +)

**Check 4: API Response**
Should get: `{"success":true,"call_id":...,"room_name":"call-..."}`

If you get error about `agent_dispatch`, the livekit-api version is wrong:
```bash
docker exec voice-agents-app-1 pip show livekit-api | grep Version
```
Should be 1.0.0 or higher

**Check 5: SIP Trunk**
Verify trunk is active in LiveKit dashboard:
https://cloud.livekit.io/projects/voice-agents-aw8yrvjs/sip

### Rebuild After Code Changes

```bash
docker compose build app
docker compose down app
docker compose up -d app
```

## Database Schema

### calls table
- `id` - Unique call ID
- `contact_id` - Links to contacts table
- `call_type` - facility_test, task_delivery, personal_message
- `status` - queued, in-progress, completed, failed
- `livekit_room_name` - LiveKit room (e.g., "call-117")
- `created_at` - When call was created
- `ended_at` - When call completed
- `custom_greeting` - What agent says first

### contacts table
- `id` - Unique contact ID
- `name` - Contact name
- `phone_number` - With + and country code
- `contact_type` - facility, friend, general

### transcript_segments table
- `call_id` - Links to calls table
- `speaker` - "agent" or "user"
- `text` - What was said
- `sequence_number` - Order of messages

## Key Files

- `app/main.py` - FastAPI server, API endpoints
- `app/scheduler_service.py` - Scheduled and recurring calls
- `livekit-agent/agent.py` - Voice agent logic
- `docker-compose.yml` - Container orchestration
- `requirements.txt` - Python packages for app container
- `livekit-agent/requirements.txt` - Packages for agent

## Success Criteria

A working system should:
1. ✅ All 3 containers running
2. ✅ API returns success with room_name
3. ✅ Phone receives call within 3-5 seconds
4. ✅ Agent speaks greeting clearly
5. ✅ Transcript saved to database
6. ✅ Call status updated to "completed"

## Current Working State (as of 2025-10-15)

- App container: livekit-api 1.0.7 ✅
- LiveKit agent: Running and registered ✅
- Database: Healthy ✅
- Last successful call: #117 to +919820754198 ✅
- Latency: 1-3 seconds ✅

## What Was Wrong (Root Cause)

The system had livekit packages installed from a previous manual installation or cached Docker layer, but:
1. `requirements.txt` didn't list them (they were installed outside package management)
2. When containers were rebuilt, Docker cache sometimes kept old versions
3. Code was written for livekit-api 1.0+ but container had 0.5.0
4. The `agent_dispatch` API doesn't exist in livekit-api 0.5.0

**Fix:** Added livekit packages to requirements.txt with correct versions and fully rebuilt container.
