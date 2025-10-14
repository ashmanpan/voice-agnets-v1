# Voice Agent System - Development Roadmap

**Last Updated:** 2025-10-15
**Current Status:** DROP 1 Complete ✅

---

## DROP Status Overview

| Drop | Status | Duration | Completion Date |
|------|--------|----------|-----------------|
| DROP 1 | ✅ Complete | 1 day | 2025-10-15 |
| DROP 2 | 📋 Planned | 2-3 days | - |
| DROP 3 | 📋 Planned | 4-5 days | - |
| DROP 4 | 📋 Planned | 3-4 days | - |

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

# DROP 2: Task Delivery System 📋 NEXT

**Goal:** Enable agent to deliver Type 1 proactive tasks during calls

**Status:** Not Started
**Estimated Duration:** 2-3 days
**Priority:** HIGH - Required for Type 1 workflow

## What We'll Build

### 1. Task-Aware Agent Mode
**File:** `livekit-agent/agent.py`

**Features:**
- [ ] Check for pending task when call starts
- [ ] Read task from database if `call_type == "task_delivery"`
- [ ] Load task details: title, description, agent_script, questions
- [ ] Inject task context into system prompt

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

### 2. Response Collection
**File:** `livekit-agent/agent.py`

**Features:**
- [ ] Capture user responses during task explanation
- [ ] Extract key information from conversation
- [ ] Store verbatim responses in `task.contact_response`
- [ ] Analyze sentiment of response
- [ ] Determine if task was completed/confirmed

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

### 3. Database Status Updates
**File:** `livekit-agent/agent.py` (background thread)

**Features:**
- [ ] Update task status: `pending` → `in_progress` (on call start)
- [ ] Update task status: `in_progress` → `completed` (on success)
- [ ] Record contact response verbatim
- [ ] Save response sentiment
- [ ] Update `task_completed` flag
- [ ] Increment `call_attempts` counter
- [ ] Set `last_attempt_at` timestamp
- [ ] Set `completed_at` if successful

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

### 5. Task-Call Integration
**File:** `app/main.py` (minor updates)

**Features:**
- [ ] When task is assigned with scheduled_time, create call with `call_type="task_delivery"`
- [ ] Link task to call via `assigned_call_id`
- [ ] Pass task_id in LiveKit metadata for agent to read

## Files to Modify

```
livekit-agent/
└── agent.py                  [MAJOR] Task reading, response collection

app/
├── main.py                   [MINOR] Task-call linking (already mostly done)
├── scheduler_service.py      [MEDIUM] Retry logic
└── models.py                 [NO CHANGE] Schema already complete
```

## Success Criteria

- [ ] Agent reads task from database correctly
- [ ] Agent delivers task message clearly and naturally
- [ ] Agent asks all questions from task
- [ ] User responses are captured accurately
- [ ] Task status updates correctly through lifecycle
- [ ] Retry logic works on call failures
- [ ] Response sentiment is analyzed
- [ ] Multiple tasks can be scheduled and executed
- [ ] No impact on agent latency (still 1-3s)

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
