# Voice Agent System - Current State Documentation

**Date:** 2025-10-15
**Status:** DROP 2 Complete, Ready for DROP 3 & 4

---

## 🎯 What's Working Right Now

### Backend System (100% Complete)

#### 1. Voice Agent with Ultra-Low Latency
- **Location:** `livekit-agent/agent.py`
- **Status:** ✅ Fully functional
- **Latency:** 1-3 seconds (maintained!)
- **Features:**
  - LiveKit + Groq LLM integration
  - Deepgram STT (Speech-to-Text)
  - OpenAI TTS (Text-to-Speech)
  - Real-time conversation handling
  - Transcript saving to database
  - Background processing (zero latency impact)

#### 2. Database Schema
- **Status:** ✅ Complete
- **Tables:**
  - `contacts` - Contact information
  - `calls` - Call records and metadata
  - `transcript_segments` - Real-time conversation segments
  - `tasks` - Type 1 Proactive tasks (user-assigned)
  - `action_items` - Type 2 Reactive actions (AI-extracted)
  - `call_analysis` - AI analysis of completed calls

#### 3. Dual Action System (DROP 1)
- **Status:** ✅ Complete
- **Type 1 - Proactive Tasks:**
  - User assigns tasks to contacts
  - Agent delivers tasks during calls
  - Collects responses and updates status
  - Task-aware system prompts
- **Type 2 - Reactive Actions:**
  - Auto-extracted from call analysis
  - Smart priority scoring
  - Sentiment-based urgency boost
  - Background processing

#### 4. Task Delivery System (DROP 2)
- **Status:** ✅ Complete and tested
- **Features:**
  - Agent loads tasks when `call_type="task_delivery"`
  - Generates dynamic task-aware prompts
  - Explicitly mentions WHO (CTO Office), WHAT, WHEN, WHY
  - Asks task-specific questions
  - Collects and analyzes responses
  - Updates task status automatically
- **Test Results:** Task 6 / Call 111 - successful delivery
- **User Feedback:** Addressed ✅

#### 5. API Endpoints
All endpoints working on `http://localhost:8001`:

**Calls:**
- `GET /api/calls` - List calls (with filters)
- `GET /api/calls/{id}` - Get call details + transcript
- `POST /api/calls/livekit-call` - Initiate normal call
- `GET /api/calls/{id}/analysis` - Get AI analysis

**Tasks (Type 1):**
- `POST /api/tasks/assign` - Assign proactive task
- `GET /api/tasks` - List tasks (with filters)
- `GET /api/tasks/{id}` - Get task details
- `PATCH /api/tasks/{id}` - Update task
- `POST /api/tasks/{task_id}/call` - Initiate task delivery call ⭐ NEW

**Actions (Type 2):**
- `GET /api/actions` - List reactive actions
- `GET /api/actions/{id}` - Get action details
- `PATCH /api/actions/{id}` - Update action

**Contacts:**
- `POST /api/contacts/upload-csv` - Bulk upload
- (Other contact endpoints exist in code)

**Webhook:**
- `POST /livekit/webhook` - Call completion handler

---

## 🖥️ Current UI (Basic HTML)

### Location
- **URL:** http://localhost:8001/
- **Files:** `app/static/index.html`, `app/static/style.css`, `app/static/app.js`

### Features
✅ **What's Working:**
1. Personal Message Call form - Make calls with custom messages
2. Facility Test Call form - Test calls to facilities
3. CSV Bulk Upload - Import contacts
4. Recent Calls list - Shows last 10 calls

❌ **What's Missing:**
1. No dashboard with statistics
2. No full contacts management
3. No transcript viewer
4. No tasks management UI
5. No actions panel UI
6. No AI analysis display
7. No call details page
8. Basic styling (not modern)

---

## 📁 Project Structure

```
voice-agents/
├── app/                          # Backend FastAPI application
│   ├── main.py                   # API server (8001)
│   ├── models.py                 # SQLAlchemy models
│   ├── database.py               # Database connection
│   ├── call_analyzer.py          # AI analysis (DROP 1)
│   ├── static/                   # Current basic UI
│   │   ├── index.html           # Main page
│   │   ├── style.css            # Styling
│   │   └── app.js               # JavaScript
│   └── migrations/               # Database migrations
│
├── livekit-agent/               # Voice agent
│   ├── agent.py                 # Main agent code (DROP 2)
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml           # Container orchestration
├── ROADMAP.md                   # DROP 2-4 specifications
├── DOCUMENTATION.md             # System architecture
├── CURRENT_STATE.md             # This file
└── README.md                    # Project overview
```

---

## 🗄️ Database Connection

**Connection String:** `postgresql://voiceagent:voiceagent123@localhost:5432/voiceagent`

**Access from host:**
```bash
psql -h localhost -p 5432 -U voiceagent -d voiceagent
# Password: voiceagent123
```

**Access from container:**
```bash
docker exec -it voice-agents-db-1 psql -U voiceagent -d voiceagent
```

---

## 🚀 Running Services

### Check Status
```bash
docker-compose ps
```

**Expected:**
- `voice-agents-app-1` - FastAPI backend (port 8001)
- `voice-agents-db-1` - PostgreSQL database (port 5432)
- `voice-agents-livekit-agent-1` - Voice agent

### Restart Services
```bash
# Restart FastAPI only
docker-compose restart app

# Restart agent only
docker-compose restart livekit-agent

# Rebuild agent after code changes
docker-compose build livekit-agent
docker-compose up -d livekit-agent

# Restart everything
docker-compose restart
```

### View Logs
```bash
# FastAPI logs
docker logs -f voice-agents-app-1

# Agent logs
docker logs -f voice-agents-livekit-agent-1

# Database logs
docker logs -f voice-agents-db-1
```

---

## 🧪 Testing

### Manual API Testing
```bash
# List recent calls
curl http://localhost:8001/api/calls

# Get call details
curl http://localhost:8001/api/calls/111

# List tasks
curl http://localhost:8001/api/tasks

# List actions
curl http://localhost:8001/api/actions

# Initiate task delivery call
curl -X POST http://localhost:8001/api/tasks/6/call
```

### Database Queries
```sql
-- List recent calls
SELECT id, contact_id, status, call_type, created_at
FROM calls
ORDER BY created_at DESC
LIMIT 10;

-- List tasks
SELECT id, title, status, priority, contact_id
FROM tasks
ORDER BY created_at DESC;

-- List actions
SELECT id, action_type, title, status, priority
FROM action_items
ORDER BY created_at DESC;

-- Get call transcript
SELECT speaker, text, sequence_number
FROM transcript_segments
WHERE call_id = 111
ORDER BY sequence_number;
```

---

## 🔑 Key Implementation Details

### Task Delivery Flow

1. **Create Task** (via API or DB):
```python
task = Task(
    contact_id=contact_id,
    title="Task title",
    description="Task description",
    task_type="reminder",
    agent_script="Script for agent to say",
    questions_to_ask='["Question 1", "Question 2"]',
    priority="high",
    status="pending",
    created_by="CTO Office",
    collect_response=True
)
```

2. **Initiate Task Delivery Call**:
```bash
curl -X POST http://localhost:8001/api/tasks/{task_id}/call
```

3. **What Happens:**
   - API creates Call with `call_type="task_delivery"` FIRST
   - Links task to call via `assigned_call_id`
   - Updates task status to "in_progress"
   - Dispatches LiveKit agent
   - Agent detects `call_type="task_delivery"`
   - Agent loads task from database
   - Agent generates task-aware system prompt
   - Agent makes call and delivers task
   - Agent collects responses
   - Agent saves response and updates status to "completed"

### Critical Sequencing
⚠️ **IMPORTANT:** The `call_type` must be set BEFORE the agent starts, otherwise the agent won't know to load the task!

```python
# CORRECT ORDER:
1. Create Call with call_type="task_delivery"
2. Link task to call
3. Dispatch agent

# WRONG ORDER (agent won't load task):
1. Create Call without call_type
2. Dispatch agent
3. Update call_type (too late!)
```

---

## 📊 System Performance

### Latency Metrics
- **STT (Speech-to-Text):** ~300ms (Deepgram Nova-2)
- **LLM (Language Model):** ~500ms (Groq Llama-3.3-70b)
- **TTS (Text-to-Speech):** ~400ms (OpenAI)
- **Total Response:** 1-3 seconds ✅

### Database Operations
- All transcript saves: Background threads (non-blocking)
- Task loading: Synchronous (acceptable - happens once per call)
- Response collection: Background thread (non-blocking)
- Call analysis: Background thread (non-blocking)

---

## 🎯 What's Next (DROP 3 & 4)

### DROP 3: Essential UI (4-5 days)
Build React + TypeScript + Tailwind frontend:

1. **Dashboard Page**
   - Call statistics cards
   - Recent calls table (20 items)
   - Real-time updates

2. **Contacts Management**
   - Full CRUD operations
   - Search and filters
   - CSV upload
   - Call history per contact

3. **Transcript Viewer**
   - Clean conversation display
   - Call metadata
   - AI analysis panel
   - Export functionality

4. **Actions Panel**
   - Two tabs: Type 1 (Tasks) | Type 2 (Actions)
   - Status filters
   - Priority sorting
   - Quick actions (mark done, call now)

### DROP 4: Advanced UI (3-4 days)

1. **Schedule Manager**
   - Calendar view
   - One-time scheduled calls
   - Recurring calls

2. **Reports & Analytics**
   - Date range selector
   - Call volume charts
   - Success rate charts
   - Sentiment distribution

3. **Bulk Operations**
   - Multi-select contacts
   - Bulk task assignment
   - Bulk call scheduling

### Future Drops (After DROP 4)

**DROP 5:** TBD - To be determined based on priorities
- Options: Task retry/scheduling, Advanced AI analysis, Call recording, Mobile UI, or Integrations

**DROP 6:** Group Calling System (2-3 days)
- Multi-participant conference calls
- Speaker identification
- Turn management
- Group call UI

**DROP 7:** Ultra-Low Latency Optimization (3-4 days) ⚡ HIGH PRIORITY
- Goal: Reduce latency from 1-3s to sub-1 second (<1000ms)
- Strategies:
  - STT optimization: Deepgram Nova-2-phonecall + streaming (300ms → 150ms)
  - LLM optimization: Dynamic model selection (8b for simple, 70b for complex)
  - TTS optimization: Cartesia Sonic or ElevenLabs Turbo (400ms → 150ms)
  - Pipeline: Parallel processing (overlap STT/LLM/TTS)
  - Network: Regional deployment + connection pooling
- Projected: 900ms average (conservative) or 550ms (aggressive)

---

## 🐛 Known Issues & Limitations

### Current Limitations
1. No retry logic for failed task delivery calls (deferred to future)
2. Simple sentiment analysis (keyword-based, not AI-powered yet)
3. No call recording/playback (only transcripts)
4. No real-time call monitoring
5. Basic UI (will be replaced in DROP 3)

### Edge Cases Handled
✅ Normal calls work perfectly (task system doesn't interfere)
✅ Task loading returns None if not a task delivery call
✅ All database operations are non-blocking
✅ Graceful error handling in agent

---

## 🔐 Environment Variables

Required in `.env`:
```bash
# Database
DATABASE_URL=postgresql://voiceagent:voiceagent123@db:5432/voiceagent

# LiveKit
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud

# Groq (for LLM)
GROQ_API_KEY=your_groq_api_key

# OpenAI (for TTS)
OPENAI_API_KEY=your_openai_api_key

# Deepgram (for STT)
DEEPGRAM_API_KEY=your_deepgram_api_key
```

---

## 📝 Git History

Recent commits:
```
36f0089 - DROP 2: Complete documentation with test results
894f03f - DROP 2: Add task delivery call endpoint
9a06786 - Update ROADMAP.md with DROP 2 commit hash
69060de - DROP 2: Task Delivery System - Enable agent to deliver proactive tasks
6878734 - Add comprehensive ROADMAP.md for DROP 2-4 tracking
0d77885 - DROP 1: Dual Action System implementation
```

---

## 🧰 Useful Commands

### Development
```bash
# Run tests (if any exist)
pytest app/tests/

# Format code
black app/ livekit-agent/

# Lint code
flake8 app/ livekit-agent/

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Debugging
```bash
# Check agent is running
docker logs --tail 50 voice-agents-livekit-agent-1

# Check API is responding
curl http://localhost:8001/health

# Check database connection
docker exec voice-agents-db-1 pg_isready -U voiceagent

# Interactive Python in container
docker exec -it voice-agents-app-1 python
```

### Cleanup
```bash
# Stop all containers
docker-compose down

# Remove volumes (WARNING: deletes database)
docker-compose down -v

# Clean Docker system
docker system prune -a
```

---

## 💡 Tips for Tomorrow

1. **Before Starting DROP 3:**
   - Read ROADMAP.md DROP 3 section thoroughly
   - Review current UI at http://localhost:8001/
   - Check all API endpoints work with curl
   - Ensure all services are running

2. **Frontend Setup:**
   - Create `frontend/` directory
   - Use Vite for React + TypeScript
   - Install Tailwind CSS
   - Setup React Router
   - Configure API client (Axios)

3. **API Integration:**
   - All backend endpoints are ready
   - Some additional endpoints may be needed (documented in ROADMAP)
   - Test API responses before building UI components

4. **Prioritization:**
   - Build Dashboard first (most visible)
   - Then Transcript Viewer (shows off AI capabilities)
   - Then Contacts Management
   - Finally Actions Panel

---

## 📚 Reference Documentation

- **ROADMAP.md** - Complete DROP 2-4 specifications with wireframes
- **DOCUMENTATION.md** - System architecture and design
- **README.md** - Project overview and setup
- **livekit-agent/agent.py** - Agent implementation with detailed comments
- **app/main.py** - All API endpoints with docstrings

---

**Last Updated:** 2025-10-15 02:58 AM
**Next Session:** DROP 3 - Essential UI Implementation
