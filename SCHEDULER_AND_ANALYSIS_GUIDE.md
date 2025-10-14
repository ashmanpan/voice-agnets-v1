# Call Scheduler & Analysis Guide

## Overview

Your voice agent system now includes:

1. **Call Scheduler** - Schedule one-time and recurring calls
2. **AI Call Analysis** - Automatically analyze call transcripts to extract:
   - Summaries
   - Action items
   - Requests
   - Complaints
   - Sentiment
   - Call outcomes
3. **Daily Reports** - Generate comprehensive reports with insights
4. **Auto-Retry** - Automatically retry failed calls

---

## Call Scheduler

### Schedule a One-Time Call

Schedule a call for a specific date/time:

```bash
curl -X POST http://localhost:8001/api/calls/schedule \
  -F "name=John Doe" \
  -F "phone=+1234567890" \
  -F "call_type=facility_test" \
  -F "scheduled_time=2025-10-15T10:00:00" \
  -F "caller_name=Krishnaji's CTO office" \
  -F "custom_greeting=Hello! This is a scheduled call."
```

**Parameters:**
- `name` (required): Contact name
- `phone` (required): Phone number
- `call_type` (required): `facility_test` or `personal_message`
- `scheduled_time` (required): ISO format datetime (YYYY-MM-DDTHH:MM:SS)
- `caller_name` (optional): Who the call is from
- `custom_greeting` (optional): Custom greeting text
- `custom_subject` (optional): Subject/purpose
- `custom_message` (optional): For personal_message type

**Response:**
```json
{
  "success": true,
  "call_id": 123,
  "scheduled_time": "2025-10-15T10:00:00",
  "message": "Call scheduled for 2025-10-15 10:00:00"
}
```

### Schedule a Recurring Call

Schedule calls that repeat daily, weekly, or monthly:

```bash
curl -X POST http://localhost:8001/api/calls/recurring \
  -F "name=John Doe" \
  -F "phone=+1234567890" \
  -F "call_type=facility_test" \
  -F "recurrence_pattern=daily" \
  -F "recurrence_time=09:00"
```

**For Weekly Calls:**
```bash
curl -X POST http://localhost:8001/api/calls/recurring \
  -F "name=John Doe" \
  -F "phone=+1234567890" \
  -F "call_type=facility_test" \
  -F "recurrence_pattern=weekly" \
  -F "recurrence_time=09:00" \
  -F "recurrence_day=monday"
```

**Parameters:**
- `recurrence_pattern` (required): `daily`, `weekly`, or `monthly`
- `recurrence_time` (required): Time in HH:MM format (24-hour)
- `recurrence_day` (required for weekly): Day name (monday, tuesday, etc.)

**Response:**
```json
{
  "success": true,
  "call_id": 124,
  "message": "Recurring call scheduled every day at 09:00"
}
```

### Manage Scheduled Calls

**Cancel a Scheduled Call:**
```bash
curl -X POST http://localhost:8001/api/calls/123/cancel
```

**Pause a Recurring Call:**
```bash
curl -X POST http://localhost:8001/api/calls/124/pause
```

**Resume a Recurring Call:**
```bash
curl -X POST http://localhost:8001/api/calls/124/resume
```

---

## Call Analysis

### Automatic Analysis

All completed calls are **automatically analyzed** when they end. The system extracts:

- **Summary**: Brief overview of the conversation
- **Action Items**: Things that need to be done
- **Requests**: Specific requests made by the user
- **Complaints**: Issues or complaints raised
- **Sentiment**: positive/neutral/negative
- **Call Outcome**: answered/voicemail/no_answer/busy

### Manual Analysis

Analyze a specific call:

```bash
curl -X POST http://localhost:8001/api/calls/63/analyze
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "call_id": 63,
    "summary": "The call was a test of the phone system, and the connection was found to be clear and stable.",
    "action_items": ["Test phone system"],
    "requests": [],
    "complaints": [],
    "sentiment": "positive",
    "call_outcome": "answered"
  }
}
```

### Get Existing Analysis

Retrieve analysis without re-analyzing:

```bash
curl http://localhost:8001/api/calls/63/analysis
```

### Analyze All Calls

Analyze all completed calls that don't have analysis yet:

```bash
curl -X POST http://localhost:8001/api/analyze-all-calls
```

**Response:**
```json
{
  "success": true,
  "analyzed_count": 47,
  "total_calls": 57,
  "errors": null
}
```

---

## Daily Reports

### Generate Today's Report (Text Format)

```bash
curl -X POST "http://localhost:8001/api/reports/daily?format=text"
```

**Output:**
```
================================================================================
📊 DAILY CALL REPORT - 2025-10-14
Generated at: 2025-10-14T08:18:50
================================================================================

📈 STATISTICS
--------------------------------------------------------------------------------
Total Calls:         23
Completed:           22
Failed/No Answer:    1
In Progress:         0
Total Duration:      1565s (26 min)
Average Duration:    71.14s

😊 SENTIMENT DISTRIBUTION
--------------------------------------------------------------------------------
Positive: 2
Neutral: 20
Negative: 0

📞 CALL OUTCOMES
--------------------------------------------------------------------------------
answered: 7
voicemail: 1
no_answer: 2
unknown: 12

💡 AGGREGATED INSIGHTS
--------------------------------------------------------------------------------
Total Action Items: 2
  • Test phone system
  • Follow up with customer

Total Requests: 2
  • May I speak with John?

Total Complaints: 1
  ⚠️  Voicemail is full

📋 INDIVIDUAL CALL DETAILS
================================================================================
[... detailed call-by-call breakdown ...]
```

### Generate Report for Specific Date

```bash
curl -X POST "http://localhost:8001/api/reports/daily?date=2025-10-13&format=text"
```

### Generate JSON Report

```bash
curl -X POST "http://localhost:8001/api/reports/daily?format=json"
```

**Response:**
```json
{
  "report_date": "2025-10-14",
  "generated_at": "2025-10-14T08:18:50",
  "statistics": {
    "total_calls": 23,
    "completed_calls": 22,
    "failed_calls": 1,
    "in_progress_calls": 0,
    "total_duration_seconds": 1565,
    "average_duration_seconds": 71.14,
    "sentiment_distribution": {
      "positive": 2,
      "neutral": 20,
      "negative": 0
    },
    "outcome_distribution": {
      "answered": 7,
      "voicemail": 1,
      "no_answer": 2,
      "unknown": 12
    }
  },
  "aggregated_insights": {
    "total_action_items": 2,
    "action_items": ["Test phone system", "Follow up"],
    "total_requests": 2,
    "requests": ["May I speak with John?"],
    "total_complaints": 1,
    "complaints": ["Voicemail is full"]
  },
  "calls": [
    {
      "call_id": 63,
      "contact_name": "Rohit",
      "phone_number": "+6585221630",
      "duration": 101,
      "status": "completed",
      "summary": "Test call to verify system",
      "action_items": ["Test phone system"],
      "requests": [],
      "complaints": [],
      "sentiment": "positive",
      "call_outcome": "answered",
      "created_at": "2025-10-14T08:00:00"
    }
    // ... more calls
  ]
}
```

### Weekly Summary Report

Get summary for last 7 days:

```bash
curl "http://localhost:8001/api/reports/summary?days=7"
```

**Response:**
```json
{
  "period": "2025-10-07 to 2025-10-14",
  "days": 7,
  "total_calls": 150,
  "daily_breakdown": {
    "2025-10-14": {
      "total": 23,
      "completed": 22,
      "failed": 1
    },
    "2025-10-13": {
      "total": 18,
      "completed": 17,
      "failed": 1
    }
    // ... more days
  }
}
```

---

## Auto-Retry Feature

The system automatically retries failed calls:

- **Default**: 3 retry attempts
- **Retry Interval**: 30 minutes between attempts
- **Configurable**: Set `max_retries` and `retry_on_no_answer` per call

**Database Fields:**
- `retry_count`: Current number of retries
- `max_retries`: Maximum retries allowed (default: 3)
- `retry_on_no_answer`: Whether to retry on no-answer (default: true)

---

## Python Examples

### Schedule a Call with Retry

```python
import requests
from datetime import datetime, timedelta

# Schedule for 1 hour from now
scheduled_time = (datetime.now() + timedelta(hours=1)).isoformat()

response = requests.post(
    "http://localhost:8001/api/calls/schedule",
    data={
        "name": "John Doe",
        "phone": "+1234567890",
        "call_type": "facility_test",
        "scheduled_time": scheduled_time,
        "caller_name": "Krishnaji's CTO office",
        "custom_greeting": "Hello! This is a scheduled test call."
    }
)

print(response.json())
```

### Generate and Save Daily Report

```python
import requests
from datetime import datetime

# Get text report
response = requests.post(
    "http://localhost:8001/api/reports/daily?format=text"
)

# Save to file
filename = f"daily_report_{datetime.now().strftime('%Y-%m-%d')}.txt"
with open(filename, 'w') as f:
    f.write(response.text)

print(f"Report saved to {filename}")
```

### Analyze Calls and Export Insights

```python
import requests
import json

# Analyze all calls
response = requests.post("http://localhost:8001/api/analyze-all-calls")
print(f"Analyzed {response.json()['analyzed_count']} calls")

# Get daily report with insights
response = requests.post("http://localhost:8001/api/reports/daily?format=json")
report = response.json()

# Extract all action items
all_action_items = report['aggregated_insights']['action_items']
print(f"\nAction Items ({len(all_action_items)}):")
for item in all_action_items:
    print(f"  • {item}")

# Extract all complaints
all_complaints = report['aggregated_insights']['complaints']
if all_complaints:
    print(f"\nComplaints ({len(all_complaints)}):")
    for complaint in all_complaints:
        print(f"  ⚠️  {complaint}")
```

---

## Database Schema

### CallAnalysis Table

Stores AI-generated insights for each call:

```sql
CREATE TABLE call_analysis (
    id SERIAL PRIMARY KEY,
    call_id INTEGER UNIQUE REFERENCES calls(id),
    summary TEXT,
    action_items TEXT,  -- JSON array
    requests TEXT,      -- JSON array
    complaints TEXT,    -- JSON array
    sentiment VARCHAR(20),  -- 'positive', 'neutral', 'negative'
    call_outcome VARCHAR(50),  -- 'answered', 'voicemail', 'no_answer', 'busy'
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Updated Calls Table

Added scheduler and retry fields:

```sql
ALTER TABLE calls
ADD COLUMN is_scheduled BOOLEAN DEFAULT FALSE,
ADD COLUMN scheduled_time TIMESTAMP,
ADD COLUMN is_recurring BOOLEAN DEFAULT FALSE,
ADD COLUMN recurrence_pattern VARCHAR(20),  -- 'daily', 'weekly', 'monthly'
ADD COLUMN recurrence_day VARCHAR(20),       -- 'monday', 'tuesday', etc.
ADD COLUMN recurrence_time VARCHAR(10),      -- 'HH:MM'
ADD COLUMN is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN retry_count INTEGER DEFAULT 0,
ADD COLUMN max_retries INTEGER DEFAULT 3,
ADD COLUMN retry_on_no_answer BOOLEAN DEFAULT TRUE;
```

---

## Use Cases

### 1. Daily Health Checks

Schedule daily calls to test your phone system:

```bash
curl -X POST http://localhost:8001/api/calls/recurring \
  -F "name=System Test" \
  -F "phone=+1234567890" \
  -F "call_type=facility_test" \
  -F "recurrence_pattern=daily" \
  -F "recurrence_time=09:00"
```

### 2. Weekly Reports

Generate weekly reports every Monday:

```bash
# Add a cron job or script that runs weekly
curl -X POST "http://localhost:8001/api/reports/summary?days=7" > weekly_report.json
```

### 3. Action Item Tracking

Extract action items from all calls:

```bash
# Analyze all calls
curl -X POST http://localhost:8001/api/analyze-all-calls

# Get report with action items
curl -X POST "http://localhost:8001/api/reports/daily?format=json" | \
  jq '.aggregated_insights.action_items[]'
```

### 4. Customer Complaint Monitoring

Track complaints across all calls:

```bash
curl -X POST "http://localhost:8001/api/reports/daily?format=json" | \
  jq '.aggregated_insights.complaints[]'
```

---

## Tips & Best Practices

1. **Schedule Calls in Recipient's Timezone**: Account for time zones when scheduling
2. **Monitor Daily Reports**: Review daily reports for patterns and insights
3. **Set Appropriate Retry Limits**: Adjust `max_retries` based on your needs
4. **Use Custom Greetings**: Personalize greetings for better engagement
5. **Regular Analysis**: Run `analyze-all-calls` periodically to ensure all calls are analyzed
6. **Export Reports**: Save daily reports for historical tracking

---

## Troubleshooting

### Analysis Returns "Analysis failed"

- Check Groq API key is valid
- Ensure transcript exists for the call
- Check app logs: `docker logs voice-agents-app-1`

### Scheduled Call Didn't Execute

- Verify scheduled_time is in the future
- Check scheduler is running: look for "📅 Call scheduler started" in logs
- Verify call status: `curl http://localhost:8001/api/calls/{call_id}`

### Report Shows No Data

- Ensure calls have been analyzed first
- Check report date is correct
- Verify calls exist for that date in database

---

## Next Steps

1. **Integrate with Email**: Send daily reports via email
2. **Dashboard**: Create web dashboard to view reports
3. **Alerts**: Set up alerts for complaints or negative sentiment
4. **Export**: Export reports to CSV or PDF
5. **Webhooks**: Send analysis results to external systems

---

For more information, see:
- [Custom Calls Guide](CUSTOM_CALLS_GUIDE.md)
- [API Documentation](README.md)
