# Call Scheduler Guide

## Overview
Schedule calls for specific times or set up recurring calls (daily, weekly, monthly) to automatically call contacts.

## Features

### One-Time Scheduled Calls
- Schedule a call for a specific date and time
- Example: Call someone at 5:00 PM today

### Recurring Calls
- **Daily**: Call every day at a specific time
- **Weekly**: Call every week on a specific day (e.g., every Sunday at 5 PM)
- **Monthly**: Call on the 1st of every month at a specific time

### Schedule Management
- **Pause**: Temporarily stop recurring calls without deleting the schedule
- **Resume**: Restart paused recurring calls
- **Cancel**: Delete a scheduled or recurring call

## API Endpoints

### 1. Schedule a One-Time Call

**POST** `/api/calls/schedule`

Schedule a call for a specific date and time.

**Parameters:**
- `name` (required): Contact name
- `phone` (required): Phone number with country code
- `call_type` (required): 'facility_test' or 'personal_message'
- `scheduled_time` (required): ISO format datetime (e.g., "2025-10-14T17:00:00")
- `caller_name` (optional): Custom caller name
- `custom_greeting` (optional): Custom greeting text
- `custom_subject` (optional): Purpose of call
- `custom_message` (optional): Message for personal_message type

**Example:**
```bash
curl -X POST "http://localhost:8001/api/calls/schedule" \
  -F "name=Daniel Clark" \
  -F "phone=+61421856756" \
  -F "call_type=facility_test" \
  -F "scheduled_time=2025-10-14T17:00:00" \
  -F "caller_name=Krishnaji's CTO office"
```

**Python Example:**
```python
import requests
from datetime import datetime, timedelta

# Schedule call for 5 PM today
scheduled_time = datetime.now().replace(hour=17, minute=0, second=0)

response = requests.post("http://localhost:8001/api/calls/schedule", data={
    "name": "Daniel Clark",
    "phone": "+61421856756",
    "call_type": "facility_test",
    "scheduled_time": scheduled_time.isoformat()
})

print(response.json())
# Output: {"success": true, "call_id": 59, "scheduled_time": "2025-10-14T17:00:00", ...}
```

### 2. Create Recurring Call

**POST** `/api/calls/recurring`

Set up a recurring call schedule.

**Parameters:**
- `name` (required): Contact name
- `phone` (required): Phone number with country code
- `call_type` (required): 'facility_test' or 'personal_message'
- `recurrence_pattern` (required): 'daily', 'weekly', or 'monthly'
- `recurrence_time` (required): Time in HH:MM format (e.g., "17:00" for 5 PM)
- `recurrence_day` (required for weekly): Day of week (e.g., "sunday", "monday")
- `caller_name` (optional): Custom caller name
- `custom_greeting` (optional): Custom greeting text
- `custom_subject` (optional): Purpose of call
- `custom_message` (optional): Message for personal_message type

**Example - Daily at 5 PM:**
```bash
curl -X POST "http://localhost:8001/api/calls/recurring" \
  -F "name=Daniel Clark" \
  -F "phone=+61421856756" \
  -F "call_type=facility_test" \
  -F "recurrence_pattern=daily" \
  -F "recurrence_time=17:00"
```

**Example - Every Sunday at 5 PM:**
```bash
curl -X POST "http://localhost:8001/api/calls/recurring" \
  -F "name=Kabeer Ahmed" \
  -F "phone=+61455906866" \
  -F "call_type=facility_test" \
  -F "recurrence_pattern=weekly" \
  -F "recurrence_day=sunday" \
  -F "recurrence_time=17:00"
```

**Python Examples:**
```python
import requests

# Daily call at 5 PM
response = requests.post("http://localhost:8001/api/calls/recurring", data={
    "name": "Daniel Clark",
    "phone": "+61421856756",
    "call_type": "facility_test",
    "recurrence_pattern": "daily",
    "recurrence_time": "17:00"
})

# Weekly call every Sunday at 5 PM
response = requests.post("http://localhost:8001/api/calls/recurring", data={
    "name": "Kabeer Ahmed",
    "phone": "+61455906866",
    "call_type": "facility_test",
    "recurrence_pattern": "weekly",
    "recurrence_day": "sunday",
    "recurrence_time": "17:00"
})

# Monthly call on 1st at 10 AM
response = requests.post("http://localhost:8001/api/calls/recurring", data={
    "name": "Hemant Sharma",
    "phone": "+14693072939",
    "call_type": "facility_test",
    "recurrence_pattern": "monthly",
    "recurrence_time": "10:00"
})
```

### 3. Pause Recurring Call

**POST** `/api/calls/{call_id}/pause`

Temporarily pause a recurring call without deleting the schedule.

**Example:**
```bash
curl -X POST "http://localhost:8001/api/calls/60/pause"
```

```python
import requests

call_id = 60
response = requests.post(f"http://localhost:8001/api/calls/{call_id}/pause")
print(response.json())
# Output: {"success": true, "message": "Recurring call paused"}
```

### 4. Resume Recurring Call

**POST** `/api/calls/{call_id}/resume`

Resume a paused recurring call.

**Example:**
```bash
curl -X POST "http://localhost:8001/api/calls/60/resume"
```

```python
import requests

call_id = 60
response = requests.post(f"http://localhost:8001/api/calls/{call_id}/resume")
print(response.json())
# Output: {"success": true, "message": "Recurring call resumed"}
```

### 5. Cancel Call

**POST** `/api/calls/{call_id}/cancel`

Cancel a scheduled or recurring call (deletes the schedule).

**Example:**
```bash
curl -X POST "http://localhost:8001/api/calls/60/cancel"
```

```python
import requests

call_id = 60
response = requests.post(f"http://localhost:8001/api/calls/{call_id}/cancel")
print(response.json())
# Output: {"success": true, "message": "Call cancelled successfully"}
```

## Use Cases

### 1. Daily Check-in Calls
Call a facility every day at the same time to verify operations:

```python
import requests

response = requests.post("http://localhost:8001/api/calls/recurring", data={
    "name": "Building A Security",
    "phone": "+61411222333",
    "call_type": "facility_test",
    "recurrence_pattern": "daily",
    "recurrence_time": "08:00",  # 8 AM daily
    "caller_name": "Facility Management",
    "custom_subject": "daily status check"
})
```

### 2. Weekly Team Calls
Call a team member every week on a specific day:

```python
import requests

response = requests.post("http://localhost:8001/api/calls/recurring", data={
    "name": "Mike Williams",
    "phone": "+14155551234",
    "call_type": "facility_test",
    "recurrence_pattern": "weekly",
    "recurrence_day": "monday",
    "recurrence_time": "09:00",  # Every Monday at 9 AM
    "caller_name": "Team Coordinator"
})
```

### 3. Monthly Reminders
Send monthly reminder calls:

```python
import requests

response = requests.post("http://localhost:8001/api/calls/recurring", data={
    "name": "Sarah Johnson",
    "phone": "+12025551234",
    "call_type": "personal_message",
    "recurrence_pattern": "monthly",
    "recurrence_time": "10:00",  # 1st of month at 10 AM
    "custom_message": "This is your monthly reminder about the team meeting."
})
```

### 4. One-Time Event Reminders
Schedule a call for a specific event:

```python
import requests
from datetime import datetime

# Schedule call for tomorrow at 3 PM
tomorrow_3pm = datetime.now().replace(hour=15, minute=0) + timedelta(days=1)

response = requests.post("http://localhost:8001/api/calls/schedule", data={
    "name": "Lisa Anderson",
    "phone": "+442071234567",
    "call_type": "personal_message",
    "scheduled_time": tomorrow_3pm.isoformat(),
    "custom_message": "Reminder: Your appointment is tomorrow at 2 PM."
})
```

## Time Format Reference

### scheduled_time (One-Time Calls)
Use ISO 8601 format: `YYYY-MM-DDTHH:MM:SS`

Examples:
- `2025-10-14T17:00:00` - October 14, 2025 at 5:00 PM
- `2025-12-25T09:30:00` - December 25, 2025 at 9:30 AM

**Python helper:**
```python
from datetime import datetime, timedelta

# Today at 5 PM
today_5pm = datetime.now().replace(hour=17, minute=0, second=0)

# Tomorrow at 10 AM
tomorrow_10am = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0)

# Next week same time
next_week = datetime.now() + timedelta(days=7)

# Format for API
scheduled_time = today_5pm.isoformat()
```

### recurrence_time (Recurring Calls)
Use 24-hour format: `HH:MM`

Examples:
- `09:00` - 9:00 AM
- `17:00` - 5:00 PM
- `13:30` - 1:30 PM
- `00:00` - Midnight
- `23:59` - 11:59 PM

### recurrence_day (Weekly Calls)
Use lowercase day names:
- `monday`
- `tuesday`
- `wednesday`
- `thursday`
- `friday`
- `saturday`
- `sunday`

## How It Works

### Persistence
- Scheduled calls are stored in the database
- When the app restarts, all active schedules are automatically reloaded
- Recurring calls continue even after server restarts

### Execution
- The scheduler runs in the background as part of the app
- Calls are executed at the exact scheduled time
- If a recurring call is paused, it won't execute but the schedule remains

### Status
- Scheduled calls have status `"scheduled"` until executed
- After execution, status changes to appropriate state (e.g., `"completed"`)
- Paused recurring calls have `is_active = false`

## Troubleshooting

### Call Not Executing at Scheduled Time
1. Check the scheduler is running: Look for "Call scheduler started" in logs
   ```bash
   docker-compose logs app | grep scheduler
   ```

2. Verify the schedule exists:
   ```bash
   docker-compose exec db psql -U voiceagent -d voiceagent -c "SELECT id, scheduled_time, is_recurring, recurrence_pattern, recurrence_time FROM calls WHERE is_scheduled = true OR is_recurring = true;"
   ```

3. Check system time zone:
   ```bash
   docker-compose exec app date
   ```

### Recurring Call Not Running
1. Verify `is_active = true`:
   ```bash
   docker-compose exec db psql -U voiceagent -d voiceagent -c "SELECT id, is_recurring, recurrence_pattern, is_active FROM calls WHERE is_recurring = true;"
   ```

2. Check if accidentally paused - resume it:
   ```bash
   curl -X POST "http://localhost:8001/api/calls/{call_id}/resume"
   ```

### Scheduled Time in Past
- Scheduled calls with times in the past won't execute
- API will reject schedules with past times
- If you need to reschedule, create a new scheduled call

## Best Practices

1. **Time Zones**: All times are in UTC. Consider time zone differences when scheduling.

2. **Testing**: Test with a nearby time first (e.g., 2 minutes from now) to verify the setup.

3. **Phone Number Format**: Always use international format with country code (+61, +1, etc.).

4. **Pause vs Cancel**: Use pause for temporary stops, cancel to permanently remove the schedule.

5. **Monitoring**: Check logs regularly to ensure calls are executing:
   ```bash
   docker-compose logs -f app | grep "Executing scheduled call"
   ```

6. **Limit Concurrent Calls**: Don't schedule too many calls at the exact same time.

## Examples

See `schedule_call_examples.py` for complete working examples.
