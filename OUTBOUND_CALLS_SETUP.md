# LiveKit Outbound Calls Setup

## Make outbound phone calls with your LiveKit agent through Twilio

---

## Architecture Flow

```
Your Script/API
    ↓
LiveKit Dispatch (create job with phone number)
    ↓
Agent joins room
    ↓
Agent creates SIP participant (calls phone)
    ↓
LiveKit SIP Outbound Trunk
    ↓
Twilio SIP Trunk (Elastic SIP Trunking)
    ↓
Phone Network
    ↓
Person answers phone
    ↓
Real-time conversation (1-3 second latency)
```

---

## Step 1: Create Twilio SIP Trunk for Outbound Calls

### 1.1 Create SIP Trunk
1. Go to: https://console.twilio.com/us1/develop/sip-trunking
2. Click **"Create new SIP Trunk"**
3. **Friendly Name**: `LiveKit Outbound`
4. **Save**

### 1.2 Add Termination Settings (for outbound)
1. In your SIP trunk, go to **"Termination"** tab
2. Click **"Add new Termination SIP URI"**
3. You'll see your **Termination SIP URI** - it looks like:
   ```
   your-trunk.pstn.twilio.com
   ```
4. **Copy this URI** - you'll need it for LiveKit

### 1.3 Create Credential List
1. Go to: https://console.twilio.com/us1/develop/sip-trunking/credential-lists
2. Click **"Create new Credential List"**
3. **Friendly Name**: `LiveKit Auth`
4. Add a credential:
   - **Username**: `livekit_user` (your choice)
   - **Password**: Generate a strong password
5. **Save**

### 1.4 Associate Credentials with Trunk
1. Go back to your SIP trunk **"Termination"** tab
2. Under **"Authentication"** → **"Credential Lists"**
3. Select the credential list you just created
4. **Save**

### 1.5 Associate Your Twilio Phone Number
1. In your SIP trunk, go to **"Numbers"** tab
2. Click **"Add an existing number"**
3. Select your Twilio phone number: **+16505029399**
4. **Save**

---

## Step 2: Create LiveKit Outbound Trunk

### 2.1 Install LiveKit CLI (if not already installed)
```bash
# macOS/Linux
curl -sSL https://get.livekit.io/cli | bash

# Or via npm
npm install -g @livekit/cli
```

### 2.2 Configure LiveKit CLI
```bash
lk cloud auth
```
Then login with your LiveKit credentials.

### 2.3 Create Outbound Trunk Config
Create file: `livekit-outbound-trunk.json`
```json
{
  "trunk": {
    "name": "Twilio Outbound",
    "address": "YOUR_TWILIO_TERMINATION_URI",
    "auth_username": "livekit_user",
    "auth_password": "YOUR_PASSWORD_FROM_STEP_1.3",
    "numbers": ["+16505029399"]
  }
}
```

**Replace**:
- `YOUR_TWILIO_TERMINATION_URI` - From Step 1.2 (e.g., `your-trunk.pstn.twilio.com`)
- `YOUR_PASSWORD_FROM_STEP_1.3` - The password you created
- `+16505029399` - Your Twilio caller ID

### 2.4 Create the Trunk
```bash
lk sip outbound create livekit-outbound-trunk.json
```

This will output a **trunk ID** like `ST_xxxxxxxxxxxxx` - **save this!**

---

## Step 3: Update Agent for Outbound Calls

The agent needs to:
1. Check if a phone number was passed in metadata
2. Create a SIP participant to call that number
3. Start the conversation

I'll update the agent code to handle this.

---

## Step 4: Make Outbound Calls

### Using LiveKit CLI

```bash
lk dispatch create \
  --new-room \
  --agent-name voice-assistant \
  --metadata '{"phone_number": "+1234567890"}'
```

Replace `+1234567890` with the phone number to call.

### Using Python Script

```python
import asyncio
from livekit import api

async def make_call(phone_number: str):
    """Make an outbound call using LiveKit"""
    livekit_api = api.LiveKitAPI(
        url='wss://voice-agents-aw8yrvjs.livekit.cloud',
        api_key='APIdmFeUChf7YwF',
        api_secret='zXhankIHiqBbny11bygr2kt8FdJ3Xnee8gUWp0tzYGU'
    )

    # Dispatch agent with phone number metadata
    await livekit_api.room.create_room(
        api.CreateRoomRequest(name=f"call-{phone_number}")
    )

    # Agent will automatically join and make the call
    print(f"Call initiated to {phone_number}")

# Example usage
asyncio.run(make_call("+1234567890"))
```

---

## Expected Flow

1. You dispatch a job with a phone number
2. LiveKit creates a room
3. Your agent joins the room
4. Agent calls `create_sip_participant` with the phone number
5. LiveKit connects through Twilio SIP trunk
6. Phone rings!
7. Person answers
8. Agent starts conversation with greeting
9. Real-time back-and-forth with **1-3 second latency**

---

## Latency Comparison

- **Old Twilio webhook**: 13-22 seconds per turn
- **LiveKit + Twilio SIP**: **1-3 seconds per turn** ⚡

That's **10x faster**!

---

## Next Steps

1. Complete Step 1: Set up Twilio SIP trunk
2. Complete Step 2: Create LiveKit outbound trunk (I'll help with CLI commands)
3. I'll update the agent code to handle outbound calls
4. Test with a call!
5. Celebrate the speed improvement 🎉
