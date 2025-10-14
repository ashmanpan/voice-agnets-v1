# Custom Call Parameters Guide

## Overview
The system now supports dynamic customization of calls with:
- **Custom Caller Name**: Change who you're calling from
- **Custom Greeting**: Completely override the default greeting
- **Custom Subject**: Add context about the purpose of the call

## API Endpoint
```
POST http://localhost:8001/api/calls/facility-test
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `name` | ✅ Yes | - | Contact name (used in greeting) |
| `phone` | ✅ Yes | - | Phone number to call |
| `caller_name` | ❌ No | "Krishnaji's CTO office" | Who you're calling from |
| `custom_greeting` | ❌ No | Auto-generated | Complete custom greeting text |
| `custom_subject` | ❌ No | "testing the phone system" | Purpose/subject of call |

## Examples

### Example 1: Default Call
```bash
curl -X POST "http://localhost:8001/api/calls/facility-test" \
  -F "name=Senthil" \
  -F "phone=+61411314178"
```
**Greeting**: "Hello! This is an AI assistant calling from Krishnaji's CTO office. May I speak with Senthil?"

---

### Example 2: Custom Caller Name
```bash
curl -X POST "http://localhost:8001/api/calls/facility-test" \
  -F "name=Senthil" \
  -F "phone=+61411314178" \
  -F "caller_name=ABC Digital Agency"
```
**Greeting**: "Hello! This is an AI assistant calling from ABC Digital Agency. May I speak with Senthil?"

---

### Example 3: Completely Custom Greeting
```bash
curl -X POST "http://localhost:8001/api/calls/facility-test" \
  -F "name=Senthil" \
  -F "phone=+61411314178" \
  -F "custom_greeting=Hi! This is Sarah from TechCorp. I wanted to follow up on your recent inquiry. Is now a good time to chat?"
```
**Greeting**: "Hi! This is Sarah from TechCorp. I wanted to follow up on your recent inquiry. Is now a good time to chat?"

---

### Example 4: Custom Caller + Subject
```bash
curl -X POST "http://localhost:8001/api/calls/facility-test" \
  -F "name=John" \
  -F "phone=+61411314178" \
  -F "caller_name=Digital Marketing Solutions" \
  -F "custom_subject=website feedback and consultation"
```
**Greeting**: "Hello! This is an AI assistant calling from Digital Marketing Solutions. May I speak with John?"
*(Subject is used in conversation context)*

---

## Python Examples

```python
import requests

API_URL = "http://localhost:8001/api/calls/facility-test"

# Default call
result = requests.post(API_URL, data={
    "name": "Senthil",
    "phone": "+61411314178"
})

# Custom caller name
result = requests.post(API_URL, data={
    "name": "Senthil",
    "phone": "+61411314178",
    "caller_name": "ABC Company Support Team"
})

# Completely custom greeting
result = requests.post(API_URL, data={
    "name": "Jane",
    "phone": "+61411314178",
    "custom_greeting": "Hi Jane! This is Sarah from XYZ Corp calling about your order. Do you have a moment?"
})

# Full customization
result = requests.post(API_URL, data={
    "name": "Mike",
    "phone": "+61411314178",
    "caller_name": "TechStartup Solutions",
    "custom_subject": "project consultation and quote"
})

print(result.json())
# Output: {"success": true, "call_id": 48, "call_sid": "CAxxxx..."}
```

---

## Use Cases

### 1. Different Business Names
Call on behalf of different companies or departments:
- "ABC Digital Agency"
- "TechCorp Support Team"
- "XYZ Marketing Department"

### 2. Personal Touch
Create warmer, more personalized greetings:
- "Hi John! This is Sarah calling about your recent order..."
- "Good afternoon! This is Mike from the customer success team..."

### 3. Context-Specific Calls
Add subject context for the conversation:
- Subject: "website feedback" → AI discusses website
- Subject: "order follow-up" → AI discusses orders
- Subject: "technical support" → AI focuses on technical issues

---

## Tips

1. **Keep greetings natural**: Don't make them too long or robotic
2. **Include the contact's name**: It personalizes the call
3. **Be clear about purpose**: Mention why you're calling early
4. **Test first**: Always test custom greetings before bulk calling

---

## Default Behavior

If you don't provide custom parameters:
- **caller_name**: Defaults to "Krishnaji's CTO office"
- **greeting**: Auto-generated as "Hello! This is an AI assistant calling from {caller_name}. May I speak with {contact_name}?"
- **subject**: Defaults to "testing the phone system"

---

## Response Format

```json
{
  "success": true,
  "call_id": 48,
  "call_sid": "CAxxxxxxxxxxxx",
  "message": "Test call initiated successfully"
}
```
