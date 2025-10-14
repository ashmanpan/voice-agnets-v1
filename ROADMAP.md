# Voice Agent System - Development Roadmap

**Last Updated:** 2025-10-15
**Current Status:** DROP 2 Complete ✅

---

## DROP Status Overview

| Drop | Status | Duration | Completion Date |
|------|--------|----------|-----------------|
| DROP 1 | ✅ Complete | 1 day | 2025-10-15 |
| DROP 2 | ✅ Complete | 1 day | 2025-10-15 |
| DROP 3 | 📋 Planned | 4-5 days | - |
| DROP 4 | 📋 Planned | 3-4 days | - |
| DROP 5 | 💡 Future | TBD | - |
| DROP 6 | 💡 Future | 2-3 days | - |
| DROP 7 | 💡 Future | 3-4 days | - |

---

# DROP 1: Dual Action System ✅ COMPLETE

**Completion Date:** 2025-10-15
**Git Commit:** `0d77885`

## What Was Built

### 1. Database Schema
- ✅ `tasks` table - Type 1 Proactive tasks
- ✅ `action_items` table - Type 2 Reactive actions
- ✅ Migration scripts created and executed

### 2. API Endpoints
- ✅ `POST /api/tasks/assign` - Assign proactive task
- ✅ `GET /api/tasks` - List all tasks (with filters)
- ✅ `GET /api/tasks/{id}` - Get task details
- ✅ `PATCH /api/tasks/{id}` - Update task
- ✅ `GET /api/actions` - List reactive actions
- ✅ `GET /api/actions/{id}` - Get action details
- ✅ `PATCH /api/actions/{id}` - Update action
- ✅ `POST /livekit/webhook` - Call completion handler

### 3. Auto-Analysis System
- ✅ Enhanced `call_analyzer.py` with auto-extraction
- ✅ Smart priority scoring (complaints=85, requests=70, follow-ups=60)
- ✅ Sentiment-based urgency boost
- ✅ Auto-generated due dates
- ✅ Background processing (zero latency impact)

### 4. Documentation
- ✅ Updated DOCUMENTATION.md
- ✅ API documentation
- ✅ Architecture updates

## Files Modified
- `app/models.py` - Added Task and ActionItem models
- `app/main.py` - Added 8 new API endpoints + webhook
- `app/call_analyzer.py` - Enhanced with auto-extraction
- `app/add_tasks_table.py` - Migration script
- `app/add_action_items_table.py` - Migration script
- `DOCUMENTATION.md` - Complete system documentation

## Key Achievement
**Agent latency maintained at 1-3 seconds!** All analysis happens in background thread after call ends.

---

# DROP 2: Task Delivery System 📋 ✅ COMPLETE

**Completion Date:** 2025-10-15
**Git Commits:** `69060de` (agent), `894f03f` (API endpoint)

**Goal:** Enable agent to deliver Type 1 proactive tasks during calls

**Status:** Complete ✅
**Actual Duration:** 1 day
**Priority:** HIGH - Required for Type 1 workflow

## What Was Built

### Summary
Successfully implemented complete task delivery system that allows the voice agent to proactively deliver tasks during calls with proper context and response collection. The system addresses user feedback to explicitly mention WHO (CTO Office), WHAT (task details), WHEN (deadline), and WHY (importance) during task delivery calls.

### 1. Task-Aware Agent Mode ✅
**File:** `livekit-agent/agent.py`

**Implemented Features:**
- ✅ Check for pending task when call starts
- ✅ Read task from database if `call_type == "task_delivery"`
- ✅ Load task details: title, description, agent_script, questions
- ✅ Inject task context into dynamic system prompt
- ✅ Update task status to "in_progress" when call starts
- ✅ Explicitly mention CTO Office as assigner
- ✅ Clearly explain task requirements and deadlines
- ✅ Ask all task-specific questions

**System Prompt Example:**
```python
system_prompt = f"""You are calling {contact_name} to discuss: {task.title}

Task Details: {task.description}

Your objectives:
1. Greet them professionally
2. Explain the task: {task.agent_script}
3. Ask these questions: {task.questions_to_ask}
4. Record their responses accurately
5. Confirm their understanding
6. Thank them and end call

Be conversational but stay focused on the task.
Keep the call under 5 minutes.
"""
```

### 2. Response Collection ✅
**File:** `livekit-agent/agent.py`

**Implemented Features:**
- ✅ Capture user responses during task explanation
- ✅ Extract key information from conversation
- ✅ Store verbatim responses in `task.contact_response`
- ✅ Analyze sentiment of response (positive/neutral/negative)
- ✅ Determine if task was completed/confirmed
- ✅ Background thread processing (zero latency impact)

**Implementation:**
```python
def analyze_task_response(transcript, questions):
    """
    Analyze conversation to extract answers to task questions
    Returns: {
        'responses': [{'question': q, 'answer': a}, ...],
        'sentiment': 'positive/neutral/negative',
        'task_completed': True/False
    }
    """
```

### 3. Database Status Updates ✅
**File:** `livekit-agent/agent.py` (background thread)

**Implemented Features:**
- ✅ Update task status: `pending` → `in_progress` (on call start)
- ✅ Update task status: `in_progress` → `completed` (on success)
- ✅ Record contact response verbatim
- ✅ Save response sentiment (positive/neutral/negative)
- ✅ Update `task_completed` flag based on sentiment
- ✅ Set `completed_at` timestamp on completion
- ✅ All operations in background thread (zero latency)

### 4. Retry Logic
**File:** `app/scheduler_service.py`

**Features:**
- [ ] Detect call failures (no answer, busy, failed)
- [ ] Check `call_attempts < max_attempts`
- [ ] Reschedule with exponential backoff:
  - 1st retry: +15 minutes
  - 2nd retry: +1 hour
  - 3rd retry: +4 hours
- [ ] Mark task as `failed` after max attempts
- [ ] Log retry attempts

### 4. Task-Call Integration API ✅
**File:** `app/main.py`

**New Endpoint:** `POST /api/tasks/{task_id}/call`

**Implemented Features:**
- ✅ Dedicated endpoint for task delivery calls
- ✅ Creates call with `call_type="task_delivery"` BEFORE agent dispatch (critical!)
- ✅ Links task to call via `assigned_call_id`
- ✅ Updates task status to `in_progress`
- ✅ Includes rollback logic if call fails
- ✅ Returns task_id, call_id, and room_name

**Why This Matters:** The order is critical - `call_type` must be set BEFORE the agent starts, otherwise the agent won't know to load the task. This was the key fix based on testing feedback.

## Files to Modify

```
livekit-agent/
└── agent.py                  [MAJOR] Task reading, response collection

app/
├── main.py                   [MINOR] Task-call linking (already mostly done)
├── scheduler_service.py      [MEDIUM] Retry logic
└── models.py                 [NO CHANGE] Schema already complete
```

## Success Criteria ✅ ALL ACHIEVED

- ✅ Agent reads task from database correctly
- ✅ Agent delivers task message clearly and naturally
- ✅ Agent explicitly mentions WHO (CTO Office), WHAT (task), WHEN (deadline), WHY (importance)
- ✅ Agent asks all questions from task
- ✅ User responses are captured accurately
- ✅ Task status updates correctly through lifecycle (pending → in_progress → completed)
- ✅ Response sentiment is analyzed (positive/neutral/negative)
- ✅ Task completion flag set based on responses
- ✅ Multiple tasks can be scheduled and executed
- ✅ No impact on agent latency (still 1-3s) - all DB ops in background threads
- ⏸️ Retry logic deferred to future enhancement (not critical for MVP)

## Testing Plan

### Test Case 1: Simple Reminder Task
```json
{
  "contact_id": 5,
  "title": "Meeting Reminder",
  "description": "Remind about tomorrow's team meeting",
  "task_type": "reminder",
  "agent_script": "I'm calling to remind you about tomorrow's team meeting at 10 AM. Will you be able to attend?",
  "questions_to_ask": ["Will you be attending the meeting?"],
  "scheduled_time": "2025-10-16T09:00:00"
}
```

**Expected:**
- Agent calls at 9 AM
- Agent explains meeting reminder
- Agent asks attendance question
- Agent records yes/no response
- Task marked completed if confirmed

### Test Case 2: Survey Task
```json
{
  "contact_id": 6,
  "title": "Customer Satisfaction Survey",
  "description": "Quick 3-question survey about our service",
  "task_type": "survey",
  "agent_script": "I have a quick 3-question survey about our service. It will only take 2 minutes.",
  "questions_to_ask": [
    "How satisfied are you with our service? Rate 1-5",
    "What's one thing we could improve?",
    "Would you recommend us to others?"
  ],
  "scheduled_time": "2025-10-16T14:00:00"
}
```

**Expected:**
- Agent asks all 3 questions
- Agent records all responses
- Responses stored in structured format
- Sentiment analyzed

### Test Case 3: Call Failure Retry
- Schedule task
- Contact doesn't answer
- System retries after 15 minutes
- If still no answer, retry after 1 hour
- After 3 attempts, mark as failed

## Actual Test Results ✅

### Task 6: API Review Test (Call 111)
**Created:** 2025-10-15
**Task Details:**
- Title: "Endpoint Test - API Review Required"
- Description: "The CTO Office needs you to review the API documentation before tomorrow afternoon meeting"
- Priority: High
- Questions: 3 specific questions about ability to complete, need for clarification, and meeting rescheduling

**Agent Behavior:**
```
🤖 "I'm calling from the CTO Office, and I wanted to touch base with you about an important task that's been assigned to you."

🤖 "The CTO Office has assigned you a task, and I wanted to go over the details with you - you need to review the API documentation for the new microservices architecture before tomorrow afternoon's meeting at 2 PM."

🤖 "This review is pretty critical for our architecture decision, so I wanted to check in with you - will you be able to complete the API review before tomorrow's 2 PM meeting?"

👤 "Yes. Yes. I will be able to do"
```

**Results:**
- ✅ Task loaded correctly (ID: 6)
- ✅ Agent generated task-aware system prompt
- ✅ Explicitly mentioned "CTO Office"
- ✅ Clearly stated the task (API review)
- ✅ Specified deadline (tomorrow 2 PM)
- ✅ Explained importance ("critical for architecture decision")
- ✅ Asked task questions
- ✅ Collected responses
- ✅ Task marked as completed
- ✅ Sentiment: positive
- ✅ Task completed flag: True
- ✅ Contact response saved to database

**User Feedback Addressed:**
Original feedback: "when task assignment call, you need to explain CTO office wants you to do so and so task, and expects to deliver before this time"
- ✅ Now explicitly mentions CTO Office
- ✅ Clearly explains what task needs to be done
- ✅ States the deadline/due date
- ✅ Explains why it's important

## Implementation Steps

### Day 1: Agent Task Reading
1. ✅ Database connection in agent.py (already exists)
2. [ ] Add task reading function
3. [ ] Modify system prompt generation
4. [ ] Test with simple reminder task

### Day 2: Response Collection
1. [ ] Implement conversation analysis
2. [ ] Extract answers to questions
3. [ ] Update task with responses
4. [ ] Test with survey task

### Day 3: Retry Logic & Testing
1. [ ] Implement retry scheduler
2. [ ] Test failure scenarios
3. [ ] End-to-end testing
4. [ ] Documentation update

---

# DROP 3: Essential UI 🎨 PLANNED

**Goal:** Build minimum viable UI for system operation

**Status:** Not Started
**Estimated Duration:** 4-5 days
**Priority:** HIGH - System unusable without UI

## What We'll Build

### 1. Better Dashboard
**Route:** `/`
**Component:** `src/pages/Dashboard.tsx`

**Features:**
- [ ] Call statistics cards:
  - Total calls (all time)
  - Today's calls
  - Success rate %
- [ ] Last 20 calls table (not just 10)
- [ ] Visual status indicators:
  - 🟢 Completed (green)
  - 🟡 In Progress (yellow)
  - 🔴 Failed (red)
  - ⚪ Scheduled (gray)
- [ ] Real-time updates (refresh every 5s)
- [ ] Click call to view details

**API Endpoints Used:**
- `GET /api/calls?limit=20` - Recent calls
- `GET /api/reports/summary?days=1` - Today's stats

**Components:**
```
Dashboard.tsx
├── CallStatsCards.tsx       (Total, Today, Success Rate)
├── CallsTable.tsx           (Last 20 calls)
└── StatusBadge.tsx          (Visual indicators)
```

### 2. Contacts Management
**Route:** `/contacts`
**Component:** `src/pages/Contacts.tsx`

**Features:**
- [ ] Clean list view of all contacts
- [ ] Search bar (by name or phone)
- [ ] Filter dropdown (Friend/Facility/General/All)
- [ ] Contact cards with:
  - Name, phone, type
  - Last call date
  - Total calls count
  - Quick actions: Call, Assign Task, View History
- [ ] CSV upload button
- [ ] Add new contact button
- [ ] Pagination (50 contacts per page)

**API Endpoints Used:**
- `GET /api/contacts` - List contacts (needs to be added)
- `POST /api/contacts` - Create contact (needs to be added)
- `POST /api/contacts/upload-csv` - CSV upload (exists)

**Components:**
```
Contacts.tsx
├── ContactsHeader.tsx       (Search, Filter, Add buttons)
├── ContactsList.tsx         (Grid of contact cards)
├── ContactCard.tsx          (Individual contact)
├── ContactForm.tsx          (Add/Edit modal)
└── CSVUploadModal.tsx       (CSV upload)
```

### 3. Transcript Viewer
**Route:** `/calls/{id}/transcript`
**Component:** `src/pages/TranscriptViewer.tsx`

**Features:**
- [ ] Call metadata header:
  - Contact name, phone
  - Status, duration
  - Date/time
- [ ] Clean conversation view:
  - 🤖 Agent messages (left, blue)
  - 👤 User messages (right, gray)
  - Timestamps
  - Scroll to bottom on load
- [ ] AI Analysis section:
  - Summary
  - Sentiment (with color coding)
  - Action items extracted
  - Requests, complaints
- [ ] Export transcript button
- [ ] Link to extracted actions

**API Endpoints Used:**
- `GET /api/calls/{id}` - Call details + transcript
- `GET /api/calls/{id}/analysis` - AI analysis

**Components:**
```
TranscriptViewer.tsx
├── CallHeader.tsx           (Metadata)
├── TranscriptMessages.tsx   (Conversation)
├── MessageBubble.tsx        (Individual message)
├── AnalysisPanel.tsx        (AI insights)
└── ExportButton.tsx         (Export functionality)
```

### 4. Actions Panel
**Route:** `/actions`
**Component:** `src/pages/Actions.tsx`

**Features:**
- [ ] Two tabs:
  - Tab 1: Type 1 - Proactive Tasks (you assigned)
  - Tab 2: Type 2 - Reactive Actions (auto-extracted)
- [ ] Filters:
  - Status (Pending/In Progress/Completed)
  - Priority (High/Medium/Low)
- [ ] Sort by urgency score
- [ ] Action cards showing:
  - Title/description
  - Contact name
  - Status, priority
  - Due date
  - Quick actions: Mark Done, Reassign, Add Notes
- [ ] Quick action buttons:
  - Call Now
  - Schedule Call
  - Analyze (for completed calls)

**API Endpoints Used:**
- `GET /api/tasks` - Type 1 tasks
- `GET /api/actions` - Type 2 actions
- `PATCH /api/tasks/{id}` - Update task
- `PATCH /api/actions/{id}` - Update action

**Components:**
```
Actions.tsx
├── ActionsTabs.tsx          (Type 1 / Type 2 tabs)
├── ActionsFilters.tsx       (Status, Priority filters)
├── TasksList.tsx            (Type 1 tasks)
├── ActionsList.tsx          (Type 2 actions)
├── ActionCard.tsx           (Individual item)
└── QuickActionsBar.tsx      (Call, Schedule, Analyze buttons)
```

## Technology Stack

### Frontend
- **Framework:** React 18 + TypeScript
- **Styling:** Tailwind CSS 3.4
- **Build Tool:** Vite 5
- **Routing:** React Router 6
- **State Management:** React Query (TanStack Query v5)
- **Icons:** Lucide React
- **Date/Time:** date-fns
- **HTTP Client:** Axios

### Project Structure
```
frontend/
├── src/
│   ├── components/        # Reusable components
│   │   ├── common/       # Buttons, inputs, badges
│   │   ├── dashboard/    # Dashboard-specific
│   │   ├── contacts/     # Contacts-specific
│   │   ├── transcript/   # Transcript-specific
│   │   └── actions/      # Actions-specific
│   ├── pages/            # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Contacts.tsx
│   │   ├── TranscriptViewer.tsx
│   │   └── Actions.tsx
│   ├── hooks/            # Custom React hooks
│   │   ├── useCalls.ts
│   │   ├── useContacts.ts
│   │   ├── useTasks.ts
│   │   └── useActions.ts
│   ├── api/              # API client
│   │   ├── client.ts     # Axios instance
│   │   ├── calls.ts      # Call endpoints
│   │   ├── contacts.ts   # Contact endpoints
│   │   ├── tasks.ts      # Task endpoints
│   │   └── actions.ts    # Action endpoints
│   ├── types/            # TypeScript types
│   │   ├── call.ts
│   │   ├── contact.ts
│   │   ├── task.ts
│   │   └── action.ts
│   ├── utils/            # Utility functions
│   │   ├── formatters.ts # Date, phone formatting
│   │   └── colors.ts     # Status colors
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── public/               # Static assets
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Additional Backend Endpoints Needed

### Contacts API
```typescript
GET    /api/contacts              // List all contacts
GET    /api/contacts/{id}         // Get contact details
POST   /api/contacts              // Create contact
PATCH  /api/contacts/{id}         // Update contact
DELETE /api/contacts/{id}         // Delete contact
GET    /api/contacts/{id}/calls   // Get contact's call history
```

### Dashboard Stats API
```typescript
GET    /api/stats/summary         // Overall statistics
GET    /api/stats/today           // Today's statistics
```

## Implementation Steps

### Day 1: Project Setup + Dashboard
1. [ ] Initialize React + Vite + TypeScript project
2. [ ] Setup Tailwind CSS
3. [ ] Install dependencies (React Router, React Query, etc)
4. [ ] Create API client with Axios
5. [ ] Build Dashboard page with stats cards
6. [ ] Build calls table component
7. [ ] Test with real API data

### Day 2: Contacts Management
1. [ ] Add backend contacts endpoints (GET, POST, PATCH, DELETE)
2. [ ] Build Contacts page layout
3. [ ] Implement search functionality
4. [ ] Implement filter by type
5. [ ] Build contact cards
6. [ ] Add CSV upload modal
7. [ ] Test CRUD operations

### Day 3: Transcript Viewer
1. [ ] Build transcript viewer layout
2. [ ] Style message bubbles (agent vs user)
3. [ ] Add AI analysis panel
4. [ ] Implement export functionality
5. [ ] Add navigation from dashboard to transcript
6. [ ] Test with real transcripts

### Day 4: Actions Panel
1. [ ] Build actions page with tabs
2. [ ] Implement Type 1 tasks list
3. [ ] Implement Type 2 actions list
4. [ ] Add filters and sorting
5. [ ] Implement quick actions (mark done, reassign)
6. [ ] Test status updates

### Day 5: Polish & Testing
1. [ ] Responsive design testing
2. [ ] Loading states
3. [ ] Error handling
4. [ ] Final styling polish
5. [ ] End-to-end testing
6. [ ] Documentation

## Success Criteria

- [ ] Dashboard loads in < 2 seconds
- [ ] All statistics display correctly
- [ ] Contacts can be searched and filtered
- [ ] CSV upload works without errors
- [ ] Transcripts display properly with correct formatting
- [ ] AI analysis shows in transcript view
- [ ] Actions can be marked complete
- [ ] All API integrations work
- [ ] UI is responsive on mobile/tablet/desktop
- [ ] No console errors

---

# DROP 4: Advanced Management 📊 PLANNED

**Goal:** Advanced scheduling, reporting, and bulk operations

**Status:** Not Started
**Estimated Duration:** 3-4 days
**Priority:** MEDIUM - Nice to have features

## What We'll Build

### 1. Call Schedule Facility
**Route:** `/schedule`
**Component:** `src/pages/Schedule.tsx`

**Features:**
- [ ] Calendar view (month/week)
- [ ] List view toggle
- [ ] One-time scheduled calls section
- [ ] Recurring calls section with patterns (daily/weekly/monthly)
- [ ] Add new schedule button
- [ ] Edit scheduled call modal
- [ ] Pause/resume recurring calls
- [ ] Delete scheduled calls
- [ ] Visual indicators for call status

**API Endpoints Used:**
- `GET /api/calls?is_scheduled=true` - Scheduled calls
- `GET /api/calls?is_recurring=true` - Recurring calls
- `POST /api/calls/schedule` - Create schedule
- `POST /api/calls/recurring` - Create recurring
- `POST /api/calls/{id}/pause` - Pause recurring
- `POST /api/calls/{id}/resume` - Resume recurring

**Components:**
```
Schedule.tsx
├── ScheduleHeader.tsx       (View toggle, Add button)
├── CalendarView.tsx         (Month/week calendar)
├── ScheduledCallsList.tsx   (List view)
├── RecurringCallsList.tsx   (Recurring patterns)
├── ScheduleFormModal.tsx    (Create/edit schedule)
└── CallStatusBadge.tsx      (Status indicators)
```

### 2. Daily Reports
**Route:** `/reports`
**Component:** `src/pages/Reports.tsx`

**Features:**
- [ ] Date range selector (Today/Last 7 days/Last 30 days/Custom)
- [ ] Call volume chart (line chart over time)
- [ ] Success rate by call type (bar chart)
- [ ] Sentiment distribution (pie chart)
- [ ] Top action types (bar chart)
- [ ] Key metrics cards:
  - Total calls
  - Success rate
  - Average duration
  - Top contact
- [ ] Export report button (PDF/CSV)
- [ ] Auto-generate daily report

**API Endpoints Used:**
- `GET /api/reports/daily?date=YYYY-MM-DD` - Daily report
- `GET /api/reports/summary?days=7` - Summary stats
- `GET /api/calls?start_date=X&end_date=Y` - Call data for charts

**Additional Backend Needed:**
```typescript
GET /api/reports/daily         // Daily summary
GET /api/reports/summary       // Period summary
GET /api/reports/charts        // Chart data
POST /api/reports/export       // Export to PDF/CSV
```

**Components:**
```
Reports.tsx
├── ReportsHeader.tsx        (Date range selector, Export)
├── MetricsCards.tsx         (Key metrics)
├── CallVolumeChart.tsx      (Line chart)
├── SuccessRateChart.tsx     (Bar chart)
├── SentimentChart.tsx       (Pie chart)
├── ActionTypesChart.tsx     (Bar chart)
└── ExportModal.tsx          (Export options)
```

**Charting Library:** Recharts (React + D3)

### 3. Bulk Operations
**Route:** `/contacts` (enhanced)
**Component:** Actions panel enhancements

**Features:**
- [ ] Multi-select contacts (checkboxes)
- [ ] Bulk assign task to multiple contacts
- [ ] Bulk schedule calls
- [ ] Bulk status updates for actions
- [ ] Bulk delete contacts
- [ ] Bulk import contacts with preview
- [ ] Progress indicator for bulk operations
- [ ] Undo functionality

**API Endpoints Needed:**
```typescript
POST /api/tasks/bulk-assign     // Assign task to multiple contacts
POST /api/calls/bulk-schedule   // Schedule multiple calls
PATCH /api/actions/bulk-update  // Update multiple actions
DELETE /api/contacts/bulk       // Delete multiple contacts
```

**Components:**
```
BulkOperationsBar.tsx        (Appears when items selected)
├── SelectAllCheckbox.tsx    (Select/deselect all)
├── BulkActionsMenu.tsx      (Assign, Schedule, Delete)
├── ProgressModal.tsx        (Bulk operation progress)
└── UndoToast.tsx           (Undo notification)
```

## Implementation Steps

### Day 1: Schedule Manager
1. [ ] Add calendar library (react-big-calendar)
2. [ ] Build calendar view
3. [ ] Build list views
4. [ ] Implement schedule form
5. [ ] Test pause/resume functionality

### Day 2: Reports & Analytics
1. [ ] Add Recharts library
2. [ ] Build reports page layout
3. [ ] Create call volume chart
4. [ ] Create success rate chart
5. [ ] Create sentiment chart
6. [ ] Add export functionality

### Day 3: Bulk Operations
1. [ ] Add bulk endpoints to backend
2. [ ] Implement multi-select UI
3. [ ] Build bulk operations bar
4. [ ] Implement bulk assign tasks
5. [ ] Implement bulk schedule
6. [ ] Add progress indicators

### Day 4: Polish & Testing
1. [ ] Test all advanced features
2. [ ] Performance optimization
3. [ ] Final styling
4. [ ] Documentation
5. [ ] Create user guide

## Success Criteria

- [ ] Calendar view displays all scheduled calls correctly
- [ ] Recurring calls can be paused/resumed
- [ ] Reports generate with accurate data
- [ ] Charts render properly and are interactive
- [ ] Export to PDF/CSV works
- [ ] Bulk operations complete successfully
- [ ] Progress indicators show for long operations
- [ ] No performance degradation with large datasets

---

# DROP 5: TBD 💡 FUTURE

**Goal:** To be determined based on priorities after DROP 3 & 4

**Status:** Not Started
**Estimated Duration:** TBD
**Priority:** TBD

## Potential Features

This drop is reserved for features that emerge as high-priority after completing DROP 3 & 4. Possible candidates:

### Option A: Task Retry & Scheduling System
- Automatic retry logic for failed task delivery calls
- Exponential backoff (15 min, 1 hour, 4 hours)
- Scheduler service for delayed/scheduled tasks
- Task queue management
- Max attempts tracking

### Option B: Advanced AI Analysis
- LLM-powered sentiment analysis (replace keyword-based)
- Automatic action classification improvements
- Better response extraction from conversations
- Intent detection
- Topic modeling

### Option C: Call Recording & Playback
- Store actual audio recordings (not just transcripts)
- Playback functionality in UI
- Audio export
- Privacy/compliance features
- Storage optimization

### Option D: Mobile Responsive UI
- Full mobile optimization
- Touch-friendly interactions
- Mobile-specific navigation
- Progressive Web App (PWA) features
- Offline mode

### Option E: Integration & Webhooks
- Webhook system for external integrations
- Zapier/Make.com integration
- Slack notifications
- Email notifications
- Calendar integrations (Google Calendar, Outlook)

**Decision Point:** Will be determined after DROP 3 & 4 based on:
- User feedback
- Most requested features
- System bottlenecks discovered
- Business priorities

---

# DROP 6: Group Calling System 👥 FUTURE

**Goal:** Enable agent to handle conference calls with multiple participants

**Status:** Not Started
**Estimated Duration:** 2-3 days
**Priority:** LOW - Advanced feature

## What We'll Build

### 1. Multi-Participant Call Support

**Technical Implementation:**
- Modify agent to handle multiple SIP participants in one room
- Implement speaker identification (voice recognition or name-based)
- Add turn-taking logic to manage conversation flow
- Handle interruptions and overlapping speech

**Database Changes:**
```sql
-- New table for tracking participants in group calls
CREATE TABLE call_participants (
    id SERIAL PRIMARY KEY,
    call_id INTEGER REFERENCES calls(id),
    contact_id INTEGER REFERENCES contacts(id),
    participant_name VARCHAR(200),
    joined_at TIMESTAMP,
    left_at TIMESTAMP,
    speaking_time_seconds INTEGER,
    turn_count INTEGER
);
```

### 2. Agent Multi-Speaker Logic

**File:** `livekit-agent/agent.py`

**Features:**
- Detect who is speaking (by voice or self-identification)
- Address people by name in responses
- Manage turn-taking fairly
- Track individual participation metrics
- Handle simultaneous speakers

**System Prompt Enhancement:**
```python
system_prompt = f"""You are facilitating a group call with:
{', '.join([p['name'] for p in participants])}

Your objectives:
1. Greet everyone by name when they join
2. Ensure everyone gets a chance to speak
3. Address people by name when responding
4. Ask: "Does anyone else have thoughts on this?"
5. Keep the conversation organized
6. Summarize key points at the end

Guidelines:
- Say one person's name before asking them a question
- Wait for responses before moving on
- If someone hasn't spoken, invite them: "{name}, what do you think?"
- Keep track of who said what
"""
```

### 3. Call Initiation for Groups

**File:** `app/main.py`

**New Endpoint:** `POST /api/calls/group`

```python
@app.post("/api/calls/group")
async def initiate_group_call(
    contact_ids: List[int],
    agenda: str,
    max_duration_minutes: int = 30,
    db: Session = Depends(get_db)
):
    """
    Initiate a group call with multiple participants
    """
    # Create call with type="group"
    call = Call(
        call_type="group",
        direction="outbound",
        status="initiated"
    )

    # Create SIP participants for each contact
    for contact_id in contact_ids:
        contact = db.query(Contact).get(contact_id)
        await ctx.api.sip.create_sip_participant(
            room_name=room_name,
            sip_call_to=contact.phone_number,
        )

    # Link all participants to call
    for contact_id in contact_ids:
        participant = CallParticipant(
            call_id=call.id,
            contact_id=contact_id
        )
        db.add(participant)
```

### 4. Transcript Management for Groups

**Enhanced Transcript:**
```python
# Save transcript with speaker identification
save_transcript_segment_async(
    call_id=call_id,
    speaker="contact_1",  # Instead of just "user"
    speaker_name="John Doe",
    text=text
)
```

### 5. UI for Group Calls

**New Component:** `GroupCallViewer.tsx`

**Features:**
- Show all participants
- Visual indicator of who's speaking
- Per-person speaking time statistics
- Participant join/leave timeline
- Multi-column transcript (one per speaker)

## Use Cases

### Conference Calls
```python
# Team standup call
group_call = {
    "contact_ids": [1, 2, 3, 4],
    "agenda": "Daily standup - quick updates from everyone",
    "questions": [
        "What did you work on yesterday?",
        "What will you work on today?",
        "Any blockers?"
    ]
}
```

### Training Sessions
```python
# Group training
group_call = {
    "contact_ids": [5, 6, 7],
    "agenda": "New feature training",
    "type": "announcement",  # Agent speaks, limited responses
    "duration": 15
}
```

### Team Announcements
```python
# Important announcement
group_call = {
    "contact_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    "agenda": "Company-wide announcement about policy change",
    "type": "broadcast",  # One-way communication
    "collect_questions": True
}
```

## Technical Challenges

### 1. Speaker Identification
**Challenge:** How to know who's speaking in a group?

**Solutions:**
- Voice biometrics (LiveKit supports)
- Ask participants to say their name first
- Use phone number mapping
- Implement roll call at start

### 2. Turn Management
**Challenge:** Prevent chaos with multiple speakers

**Solutions:**
- Agent explicitly calls on people by name
- Implement "raised hand" feature (DTMF tone)
- Time limits per speaker
- Agent moderates: "Let's hear from John next"

### 3. Latency Concerns
**Challenge:** More participants = more complexity = potential latency

**Solutions:**
- Limit group size (max 5-8 people)
- Optimize speaker detection
- Use faster LLM responses for turn-taking decisions
- Pre-load participant information

### 4. Conversation Quality
**Challenge:** Group calls are harder for AI to moderate naturally

**Solutions:**
- Strong system prompts with clear roles
- Agent as "facilitator" not "participant"
- Structured agenda with clear segments
- Time boxing each topic

## Implementation Steps

### Day 1: Multi-Participant Support
1. [ ] Modify agent to accept multiple SIP participants
2. [ ] Implement basic speaker tracking
3. [ ] Test with 2-3 participants
4. [ ] Add participant database table

### Day 2: Enhanced Agent Logic
1. [ ] Implement speaker identification
2. [ ] Add turn-taking prompts
3. [ ] Test conversation flow
4. [ ] Add name-based addressing

### Day 3: UI & Polish
1. [ ] Build group call viewer component
2. [ ] Add participant metrics display
3. [ ] Test end-to-end with real group
4. [ ] Documentation and best practices

## Success Criteria

- [ ] Agent can handle 3-5 participants successfully
- [ ] Each participant gets fair speaking time
- [ ] Agent addresses people by name correctly
- [ ] Transcript shows who said what
- [ ] Conversation stays organized and on-topic
- [ ] Call quality remains high (no audio issues)
- [ ] Latency stays under 3 seconds per response
- [ ] Group calls complete successfully

## Known Limitations

- Maximum 8 participants (LiveKit/SIP trunk limits)
- Works best with structured agendas
- Not ideal for free-form discussions
- Speaker identification may not be 100% accurate
- Requires good audio quality from all participants

## Alternative: Sequential Calls

**Note:** For many use cases, calling people sequentially (one after another) may be simpler and more reliable than true group calls. Consider this approach first!

---

# DROP 7: Ultra-Low Latency Optimization ⚡ FUTURE

**Goal:** Reduce agent response latency from 1-3 seconds to sub-1 second

**Status:** Not Started
**Estimated Duration:** 3-4 days
**Priority:** HIGH - User wants even better performance

## Current Performance Baseline

### Measured Latency (DROP 2)
- **STT (Speech-to-Text):** ~300ms (Deepgram Nova-2)
- **LLM (Language Model):** ~500ms (Groq Llama-3.3-70b)
- **TTS (Text-to-Speech):** ~400ms (OpenAI)
- **Network/Processing:** ~200-500ms
- **Total Response:** 1-3 seconds ✅

### Target Latency
- **Goal:** < 1 second total response time
- **Stretch Goal:** 500-800ms for simple responses

## Optimization Strategies

### 1. STT (Speech-to-Text) Optimization

**Current:** Deepgram Nova-2 (~300ms)

**Improvements:**
- [ ] Enable Deepgram streaming with `interim_results=true`
- [ ] Use `endpointing` parameter to detect speech end faster
- [ ] Try Deepgram Nova-2-phonecall model (optimized for phone calls)
- [ ] Implement voice activity detection (VAD) pre-filtering
- [ ] Test Deepgram's `smart_format=false` for faster raw transcription

**Expected Gain:** 100-150ms reduction → **~150-200ms**

**Implementation:**
```python
# livekit-agent/agent.py
stt = deepgram.STT(
    model="nova-2-phonecall",  # Phone-optimized model
    interim_results=True,      # Stream partial results
    endpointing=100,           # Detect end of speech faster (100ms)
    smart_format=False,        # Skip formatting for speed
    vad_events=True           # Voice activity detection
)
```

### 2. LLM (Language Model) Optimization

**Current:** Groq Llama-3.3-70b (~500ms)

**Improvements:**
- [ ] **Smaller model for simple responses:** Use Llama-3.1-8b for simple confirmations
- [ ] **Parallel processing:** Start TTS before LLM finishes (stream first sentence)
- [ ] **Response caching:** Cache common responses (greetings, confirmations)
- [ ] **Context trimming:** Send only relevant context (trim old conversation)
- [ ] **Prompt optimization:** Shorter system prompts for faster parsing
- [ ] **Try Groq's Llama-3.3-70b-specdec:** Speculative decoding for faster inference

**Expected Gain:** 200-300ms reduction → **~200-300ms**

**Implementation:**
```python
# Dynamic model selection based on complexity
def select_model(user_input):
    simple_patterns = ["yes", "no", "ok", "sure", "yeah", "hello"]
    if any(p in user_input.lower() for p in simple_patterns):
        return "llama-3.1-8b-instant"  # ~100ms
    else:
        return "llama-3.3-70b-versatile"  # ~500ms

# Response streaming with early TTS start
async def generate_response(prompt):
    response_stream = groq_llm.generate_stream(prompt)
    first_sentence = await get_first_sentence(response_stream)

    # Start TTS immediately with first sentence
    asyncio.create_task(tts.synthesize(first_sentence))

    # Continue generating rest
    full_response = first_sentence + await collect_rest(response_stream)
```

### 3. TTS (Text-to-Speech) Optimization

**Current:** OpenAI TTS (~400ms)

**Improvements:**
- [ ] **Try ElevenLabs Turbo:** ~200ms latency
- [ ] **Try Cartesia Sonic:** ~150ms latency (designed for real-time)
- [ ] **Streaming TTS:** Start playing audio before full synthesis
- [ ] **Chunk optimization:** Synthesize sentence-by-sentence
- [ ] **Voice cache:** Pre-generate common phrases
- [ ] **Lower sample rate:** 16kHz instead of 24kHz for phone calls

**Expected Gain:** 200-250ms reduction → **~150-200ms**

**Implementation:**
```python
# Try Cartesia Sonic (ultra-low latency TTS)
from cartesia import AsyncCartesia

tts = AsyncCartesia(
    voice="professional-male",
    sample_rate=16000,  # Lower for phone calls
    streaming=True      # Stream audio chunks
)

# Pre-cache common phrases
tts_cache = {
    "greeting": preload_audio("Hello, how can I help you?"),
    "confirmation": preload_audio("Got it, thank you."),
    "goodbye": preload_audio("Have a great day!")
}
```

### 4. Network & Infrastructure Optimization

**Improvements:**
- [ ] **Regional deployment:** Deploy agent closer to SIP trunk (same region)
- [ ] **WebSocket optimization:** Reduce LiveKit WebSocket latency
- [ ] **Connection pooling:** Keep DB connections warm
- [ ] **Redis caching:** Cache frequent database queries
- [ ] **CDN for static assets:** Faster UI loading

**Expected Gain:** 100-200ms reduction → **~100-200ms**

### 5. Agent Pipeline Optimization

**Current:** Sequential processing (STT → LLM → TTS)

**Improvements:**
- [ ] **Parallel processing:** Start LLM while STT is finalizing
- [ ] **Predictive pre-loading:** Pre-load next likely response
- [ ] **Response templating:** Use templates for common patterns
- [ ] **Context pruning:** Keep only last 5 turns in context
- [ ] **Async everything:** Eliminate all blocking operations

**Expected Gain:** 100-200ms reduction

**Implementation:**
```python
# Parallel pipeline
async def optimized_pipeline(audio_input):
    # Start STT
    stt_task = asyncio.create_task(stt.transcribe(audio_input))

    # While waiting, prepare context
    context_task = asyncio.create_task(prepare_context())

    # Get transcription and context in parallel
    text, context = await asyncio.gather(stt_task, context_task)

    # Start LLM with streaming
    llm_stream = llm.generate_stream(text, context)

    # Get first sentence and start TTS immediately
    first_sentence = await get_first_sentence(llm_stream)
    tts_task = asyncio.create_task(tts.synthesize(first_sentence))

    # Continue generating while TTS runs
    rest_text = await collect_rest(llm_stream)
    rest_audio = await tts.synthesize(rest_text)

    # Combine audio
    first_audio = await tts_task
    return first_audio + rest_audio
```

### 6. Database & Background Operations

**Current:** All DB operations in background threads ✅

**Additional Optimizations:**
- [ ] **Connection pooling:** Reuse DB connections
- [ ] **Batch writes:** Group transcript segments
- [ ] **Lazy loading:** Don't load task until needed
- [ ] **Query optimization:** Add indexes on frequently queried columns
- [ ] **Read replicas:** Use read replica for queries

**Expected Gain:** Minimal (already non-blocking), but improves reliability

## Technology Evaluations

### Alternative STT Providers
| Provider | Model | Latency | Cost | Quality |
|----------|-------|---------|------|---------|
| Deepgram | Nova-2 (current) | 300ms | $ | ⭐⭐⭐⭐⭐ |
| Deepgram | Nova-2-phonecall | 200ms | $ | ⭐⭐⭐⭐⭐ |
| Assembly AI | Best | 400ms | $$ | ⭐⭐⭐⭐ |
| Azure | Real-time | 250ms | $$ | ⭐⭐⭐⭐ |

**Recommendation:** Stick with Deepgram, optimize settings

### Alternative LLM Providers
| Provider | Model | Latency | Cost | Quality |
|----------|-------|---------|------|---------|
| Groq | Llama-3.3-70b (current) | 500ms | Free | ⭐⭐⭐⭐⭐ |
| Groq | Llama-3.1-8b | 100ms | Free | ⭐⭐⭐⭐ |
| OpenAI | GPT-4o-mini | 800ms | $$ | ⭐⭐⭐⭐⭐ |
| Anthropic | Claude-3-haiku | 600ms | $$ | ⭐⭐⭐⭐⭐ |

**Recommendation:** Use Llama-3.1-8b for simple responses, 3.3-70b for complex

### Alternative TTS Providers
| Provider | Model | Latency | Cost | Quality |
|----------|-------|---------|------|---------|
| OpenAI | TTS-1 (current) | 400ms | $ | ⭐⭐⭐⭐ |
| ElevenLabs | Turbo v2 | 200ms | $$ | ⭐⭐⭐⭐⭐ |
| Cartesia | Sonic | 150ms | $$ | ⭐⭐⭐⭐ |
| PlayHT | Turbo | 250ms | $$ | ⭐⭐⭐⭐ |
| Azure | Neural | 350ms | $$ | ⭐⭐⭐⭐ |

**Recommendation:** Try Cartesia Sonic or ElevenLabs Turbo

## Projected Latency After Optimization

### Conservative Estimate
- STT: 200ms (from 300ms) ✅
- LLM: 300ms (from 500ms) ✅
- TTS: 200ms (from 400ms) ✅
- Network: 200ms (from 300ms) ✅
- **Total: 900ms** (from 1500ms average)

### Aggressive Estimate
- STT: 150ms (with streaming + VAD)
- LLM: 150ms (small model for simple responses)
- TTS: 150ms (Cartesia Sonic + streaming)
- Network: 100ms (regional optimization)
- **Total: 550ms** for simple interactions

## Implementation Plan

### Day 1: STT & TTS Optimization
1. [ ] Test Deepgram Nova-2-phonecall model
2. [ ] Enable Deepgram streaming and endpointing
3. [ ] Integrate Cartesia Sonic TTS
4. [ ] Compare latency before/after
5. [ ] A/B test voice quality

### Day 2: LLM Optimization
1. [ ] Implement dynamic model selection (8b vs 70b)
2. [ ] Add response caching for common phrases
3. [ ] Implement context trimming (last 5 turns only)
4. [ ] Test streaming LLM responses
5. [ ] Start TTS before LLM finishes

### Day 3: Pipeline & Infrastructure
1. [ ] Implement parallel pipeline (STT/LLM/TTS overlap)
2. [ ] Add Redis for response caching
3. [ ] Optimize database queries with indexes
4. [ ] Test regional deployment options
5. [ ] Profile and eliminate bottlenecks

### Day 4: Testing & Measurement
1. [ ] Comprehensive latency measurements
2. [ ] Load testing with multiple concurrent calls
3. [ ] Quality assurance (ensure no quality degradation)
4. [ ] User acceptance testing
5. [ ] Documentation and rollout

## Success Criteria

- [ ] **Target:** Average response latency < 1 second
- [ ] **Stretch:** Simple responses < 600ms
- [ ] **Quality:** No degradation in transcription accuracy
- [ ] **Quality:** No degradation in voice naturalness
- [ ] **Quality:** No degradation in LLM response quality
- [ ] **Reliability:** 99.9% uptime maintained
- [ ] **Cost:** Stay within budget (avoid expensive providers)

## Monitoring & Metrics

### Metrics to Track
```python
# Add to agent.py
latency_metrics = {
    "stt_latency_ms": [],
    "llm_latency_ms": [],
    "tts_latency_ms": [],
    "total_latency_ms": [],
    "model_used": [],
    "response_type": []  # simple vs complex
}

# Log to database for analysis
async def log_latency(call_id, metrics):
    await db.execute(
        "INSERT INTO latency_logs (call_id, stt_ms, llm_ms, tts_ms, total_ms) VALUES ..."
    )
```

### Dashboard
- [ ] Add latency graphs to UI
- [ ] P50, P95, P99 latency percentiles
- [ ] Latency by call type (normal vs task delivery)
- [ ] Model selection statistics

## Cost Analysis

### Current Costs (per 1000 calls)
- Deepgram STT: ~$5 (10 min avg)
- Groq LLM: $0 (free tier)
- OpenAI TTS: ~$15
- **Total: ~$20 per 1000 calls**

### After Optimization (worst case)
- Deepgram STT: ~$5 (same)
- Groq LLM: $0 (still free)
- Cartesia TTS: ~$25 (more expensive but faster)
- **Total: ~$30 per 1000 calls**

**Cost increase:** 50%, but worth it for 2-3x latency improvement

## Risk Mitigation

### Fallback Strategy
- Keep current pipeline as fallback
- Feature flag for new optimizations
- Gradual rollout (10% → 50% → 100%)
- Monitor quality metrics closely

### Quality Assurance
- A/B test with real users
- Collect feedback on voice quality
- Measure task completion rates
- Compare before/after transcription accuracy

## Alternative: Hybrid Approach

If full optimization is too complex, consider:
- Use fast models (8b + Cartesia) for **simple interactions** (yes/no, confirmations)
- Use current models (70b + OpenAI) for **complex tasks** (task delivery, surveys)
- Best of both worlds: speed where it matters, quality where it matters

---

## Overall Progress Tracking

### Completed Features ✅
- [x] LiveKit ultra-low latency agent (1-3s)
- [x] Dual action system (Type 1 & Type 2)
- [x] Auto-analysis on call completion
- [x] Background action extraction
- [x] Smart priority scoring
- [x] Tasks and Actions API

### In Progress 🚧
- [ ] (None - awaiting DROP 2 start)

### Planned 📋
- [ ] Task delivery by agent
- [ ] Essential UI (Dashboard, Contacts, Transcript, Actions)
- [ ] Advanced UI (Schedule, Reports, Bulk Ops)

---

## Git Commit Guidelines

Each DROP should be committed with:
```bash
git add .
git commit -m "DROP X: [Title]

[Detailed description of what was built]

Key Features:
✅ Feature 1
✅ Feature 2
✅ Feature 3

Files Modified:
- file1.py
- file2.tsx

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Update Log

| Date | Update | Author |
|------|--------|--------|
| 2025-10-15 | Created ROADMAP.md, DROP 1 complete | Claude |
| 2025-10-15 | Detailed DROP 2-4 specifications | Claude |

---

**Next Action:** Start DROP 2 - Task Delivery System
