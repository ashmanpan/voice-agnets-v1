# Tomorrow's Action Plan - LiveKit Voice Agent Setup

**Estimated Total Time**: 25 minutes
**Goal**: Make outbound calls with 1-3 second latency

---

## ✅ Before You Start - Verify Setup

```bash
cd /home/kpanse/wsl-myprojects/voice-agents

# Check agent is running
docker-compose ps

# View agent logs
docker-compose logs --tail=20 livekit-agent
```

**Expected**: You should see `"registered worker"` message.

If agent is not running:
```bash
docker-compose up -d livekit-agent
```

---

## 📋 Step 1: Set Up Twilio SIP Trunk (10 minutes)

### 1.1 Create SIP Trunk

1. Go to: **https://console.twilio.com/us1/develop/sip-trunking**

2. Click **"Create new SIP Trunk"**

3. Settings:
   - **Friendly Name**: `LiveKit Outbound`
   - Click **"Create"**

4. **Copy the Trunk SID** (starts with `TK...`)
   - Save it: `TK_____________________________`

### 1.2 Configure Termination (Outbound)

1. In your new trunk, click **"Termination"** tab

2. You'll see **"Termination SIP URI"**
   - It looks like: `your-trunk-name.pstn.twilio.com`
   - **Copy this entire URI**: _______________________________________
   - ⚠️ **IMPORTANT**: Save this, you'll need it for LiveKit

3. Click **"+"** under Termination SIP URIs to enable it

### 1.3 Create Credential List

1. Go to: **https://console.twilio.com/us1/develop/sip-trunking/credential-lists**

2. Click **"Create new Credential List"**

3. Settings:
   - **Friendly Name**: `LiveKit Auth`
   - Click **"Create"**

4. Click **"Add a Credential"**

5. Create credentials:
   - **Username**: `livekit_user` (or your choice)
   - **Password**: Create a strong password (or use generator)
   - Click **"Save"**

6. **Copy these credentials**:
   ```
   Username: _______________________________
   Password: _______________________________
   ```

### 1.4 Associate Credentials with Trunk

1. Go back to: **https://console.twilio.com/us1/develop/sip-trunking**

2. Click on your **"LiveKit Outbound"** trunk

3. Click **"Termination"** tab

4. Scroll to **"Authentication"** section

5. Under **"Credential Lists"**:
   - Click the dropdown
   - Select `LiveKit Auth` (the credential list you created)
   - Click **"Save"**

### 1.5 Associate Phone Number

1. Still in your trunk, click **"Numbers"** tab

2. Click **"Add an existing number"**

3. Select: **+16505029399**

4. Click **"Add"**

### ✅ Checkpoint 1

You should now have:
- ✅ SIP Trunk created (Trunk SID: `TK...`)
- ✅ Termination URI copied (e.g., `your-trunk.pstn.twilio.com`)
- ✅ Credentials created (username & password)
- ✅ Credentials associated with trunk
- ✅ Phone number associated with trunk

---

## 📋 Step 2: Install LiveKit CLI (5 minutes)

### 2.1 Install CLI

```bash
# Install via script (recommended)
curl -sSL https://get.livekit.io/cli | bash

# Verify installation
lk --version
```

**Alternative** if script doesn't work:
```bash
npm install -g @livekit/cli
```

### 2.2 Authenticate with LiveKit Cloud

```bash
lk cloud auth
```

This will open a browser for you to log in to LiveKit Cloud.

**Credentials**:
- Email: (your LiveKit account email)
- Password: (your LiveKit account password)

### ✅ Checkpoint 2

You should see: `Successfully authenticated with LiveKit Cloud`

---

## 📋 Step 3: Create LiveKit Outbound Trunk (5 minutes)

### 3.1 Create Trunk Configuration File

```bash
cd /home/kpanse/wsl-myprojects/voice-agents
nano livekit-outbound-trunk.json
```

Paste this (replace the placeholders):
```json
{
  "trunk": {
    "name": "Twilio Outbound",
    "address": "YOUR_TERMINATION_URI_FROM_STEP_1.2",
    "auth_username": "YOUR_USERNAME_FROM_STEP_1.3",
    "auth_password": "YOUR_PASSWORD_FROM_STEP_1.3",
    "numbers": ["+16505029399"]
  }
}
```

**Replace**:
- `YOUR_TERMINATION_URI_FROM_STEP_1.2` → The Twilio termination SIP URI (e.g., `livekit-trunk.pstn.twilio.com`)
- `YOUR_USERNAME_FROM_STEP_1.3` → The username you created (e.g., `livekit_user`)
- `YOUR_PASSWORD_FROM_STEP_1.3` → The password you created

**Example**:
```json
{
  "trunk": {
    "name": "Twilio Outbound",
    "address": "livekit-trunk.pstn.twilio.com",
    "auth_username": "livekit_user",
    "auth_password": "mySecurePassword123!",
    "numbers": ["+16505029399"]
  }
}
```

Save and exit (Ctrl+X, Y, Enter)

### 3.2 Create the Outbound Trunk

```bash
lk sip outbound create livekit-outbound-trunk.json
```

**Expected output**:
```
Created outbound trunk: ST_xxxxxxxxxxxxx
```

**⚠️ IMPORTANT**: Copy the trunk ID (starts with `ST_`):
```
Trunk ID: ST_____________________________
```

### 3.3 Verify Trunk

```bash
lk sip outbound list
```

You should see your trunk listed with status "Active".

### ✅ Checkpoint 3

You should have:
- ✅ LiveKit CLI installed and authenticated
- ✅ Outbound trunk created
- ✅ Trunk ID saved (starts with `ST_`)

---

## 📋 Step 4: Make Test Call! (5 minutes)

### 4.1 Prepare the Call Script

```bash
cd /home/kpanse/wsl-myprojects/voice-agents/livekit-agent
```

The script is already created: `make_call.py`

### 4.2 Make the Call

**Syntax**:
```bash
python make_call.py <phone_number> <trunk_id>
```

**Example** (replace with your number and trunk ID):
```bash
python make_call.py +1234567890 ST_xxxxxxxxxxxxx
```

**What happens**:
1. Script creates a LiveKit room
2. Agent joins the room
3. Agent initiates SIP call through Twilio
4. Your phone rings!
5. Answer and have a conversation

### 4.3 Monitor the Call

In another terminal:
```bash
docker-compose logs -f livekit-agent
```

You should see:
- `connecting to room call-XXXXX`
- `Outbound call metadata: phone=+1234567890`
- `Initiating outbound call to +1234567890`
- `SIP participant created`
- Conversation transcripts in real-time

### 4.4 Measure Latency

During the call, **mentally note** the time between:
- You stop speaking
- AI starts responding

**Target**: 1-3 seconds (vs 20 seconds with old webhook)

### ✅ Checkpoint 4

You should have:
- ✅ Made a successful outbound call
- ✅ Had a conversation with the AI
- ✅ Noticed significantly lower latency
- ✅ Seen logs showing the conversation

---

## 📋 Step 5: Compare with Old System (Optional - 5 minutes)

### Test the Old Webhook System

Call your Twilio number: **+16505029399**

The old webhook system is still running and will answer.

**Compare**:
- Old system: ~20 seconds per turn
- New system: ~1-3 seconds per turn

---

## 🐛 Troubleshooting

### Issue: CLI command not found

**Solution**:
```bash
# Try npm install
npm install -g @livekit/cli

# Or add to path
export PATH=$PATH:$HOME/.livekit
```

### Issue: Authentication failed

**Solution**:
```bash
# Re-authenticate
lk cloud auth

# Or use explicit credentials
lk sip outbound create \
  --url wss://voice-agents-aw8yrvjs.livekit.cloud \
  --api-key APIdmFeUChf7YwF \
  --api-secret zXhankIHiqBbny11bygr2kt8FdJ3Xnee8gUWp0tzYGU \
  livekit-outbound-trunk.json
```

### Issue: Call doesn't connect

**Check**:
1. Trunk ID is correct in make_call.py command
2. Phone number format is correct (+1234567890)
3. Twilio trunk has phone number associated
4. Agent is running: `docker-compose ps`

**View Twilio logs**:
- Go to: https://console.twilio.com/us1/monitor/logs/calls

### Issue: No audio or one-way audio

**Check**:
1. Credentials in trunk config match Twilio
2. Termination SIP URI is correct
3. Trunk is "Active" in `lk sip outbound list`

### Issue: Agent doesn't join room

**Solution**:
```bash
# Restart agent
docker-compose restart livekit-agent

# Check logs
docker-compose logs --tail=50 livekit-agent
```

---

## 📝 Summary Checklist

Before you finish, verify:

- [ ] Twilio SIP trunk created and configured
- [ ] Twilio credentials created and associated
- [ ] Phone number associated with trunk
- [ ] LiveKit CLI installed and authenticated
- [ ] LiveKit outbound trunk created
- [ ] Trunk ID saved
- [ ] Successfully made test call
- [ ] Measured latency (~1-3 seconds)
- [ ] Compared with old system (~20 seconds)

---

## 🎉 Success Criteria

You'll know it's working when:

1. **Call connects within 5 seconds**
2. **AI greets you**: "Hello! This is an AI assistant calling from Krishnaji's CTO office..."
3. **You can have a conversation**
4. **Response time is 1-3 seconds** (vs 20 before)
5. **Conversation feels natural and real-time**

---

## 📞 After Success - Next Steps

### Make Multiple Test Calls

```bash
# Call different numbers
python make_call.py +1234567890 ST_xxxxx
python make_call.py +0987654321 ST_xxxxx
```

### Monitor in LiveKit Dashboard

https://cloud.livekit.io/projects/voice-agents-aw8yrvjs/rooms

You'll see active rooms and can monitor:
- Participants
- Audio quality
- Connection stats

### Integrate into Your Application

Once confirmed working, you can:
1. Create a web interface to make calls
2. Build a call queue system
3. Add call recording
4. Implement call analytics
5. Scale to multiple agents

---

## 🆘 Need Help?

### Check Documentation

- `PROJECT_STATUS.md` - Complete project overview
- `OUTBOUND_CALLS_SETUP.md` - Detailed setup guide
- `livekit-agent/README.md` - Agent documentation

### View Logs

```bash
# Agent logs
docker-compose logs -f livekit-agent

# All services
docker-compose logs -f
```

### Useful Commands

```bash
# List outbound trunks
lk sip outbound list

# Check agent status
docker-compose ps

# Restart everything
docker-compose restart

# Stop everything
docker-compose down

# Start fresh
docker-compose up -d
```

---

## 🎯 Timeline

| Step | Task | Time |
|------|------|------|
| 1 | Set up Twilio SIP trunk | 10 min |
| 2 | Install LiveKit CLI | 5 min |
| 3 | Create LiveKit outbound trunk | 5 min |
| 4 | Make test call | 5 min |
| 5 | Compare with old system | 5 min |
| **Total** | | **30 min** |

---

## 💪 You've Got This!

Everything is ready on the code side. Tomorrow is just configuration:

1. ✅ Agent is built and running
2. ✅ Code supports outbound calls
3. ✅ Scripts are ready to use
4. ✅ Documentation is complete

Just follow the steps above and you'll have **10x faster voice calls** in 30 minutes!

Good luck! 🚀
