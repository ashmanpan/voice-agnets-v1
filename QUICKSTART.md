# Quick Start Guide

Get your voice agent running in 10 minutes!

## Prerequisites Checklist

- [ ] Docker Desktop installed and running
- [ ] Twilio account (free trial works)
- [ ] OpenAI API key
- [ ] ngrok installed (free tier)

## Step-by-Step Setup

### 1. Get Twilio Credentials (5 minutes)

1. Go to https://www.twilio.com/try-twilio
2. Sign up for free trial ($15 credit)
3. Get a phone number:
   - Go to Phone Numbers → Buy a Number
   - Choose one with Voice capability
   - Cost: ~$1/month
4. Find your credentials:
   - Dashboard → Account Info
   - Copy **Account SID**
   - Copy **Auth Token**

### 2. Get OpenAI API Key (2 minutes)

1. Go to https://platform.openai.com
2. Sign up / Log in
3. Add payment method (required)
4. Create API key:
   - Settings → API Keys
   - Create new secret key
   - Copy and save it (shown only once!)

### 3. Install ngrok (1 minute)

```bash
# Mac
brew install ngrok

# Linux
sudo snap install ngrok

# Or download from: https://ngrok.com/download
```

Sign up and authenticate:
```bash
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

### 4. Configure Environment (1 minute)

```bash
cd voice-agents
cp .env.example .env
nano .env  # or use any text editor
```

Update these values:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxx

# Leave this for now, update after starting ngrok
PUBLIC_URL=https://your-url.ngrok.io
```

### 5. Start ngrok (30 seconds)

Open a **separate terminal** and run:
```bash
ngrok http 8000
```

You'll see:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** and update `PUBLIC_URL` in your `.env`:
```env
PUBLIC_URL=https://abc123.ngrok.io
```

**Keep this terminal running!**

### 6. Start the Voice Agent (1 minute)

```bash
# Make setup script executable
chmod +x scripts/setup.sh

# Run setup
./scripts/setup.sh
```

Or manually:
```bash
docker-compose build
docker-compose up
```

Wait for:
```
✅ Database initialized
✅ Application started
```

### 7. Open Dashboard

Go to: http://localhost:8000

You should see the Voice Agent Dashboard!

## Make Your First Call

### Test with Your Own Phone

1. Click "Personal Message Call"
2. Enter:
   - **Name**: Your Name
   - **Phone**: Your phone number (with country code!)
   - **Message**: "This is a test call from my voice agent!"
3. Click "Make Call Now"
4. **Answer your phone!**
5. The agent will deliver your message

### Expected Call Flow

```
📞 Your phone rings

You: "Hello?"

Agent: "Hi, may I speak with [Your Name]?"

You: "Yes, speaking"

Agent: "Hi! My name is SOS and I want to give you an update:
       This is a test call from my voice agent!"

Agent: "Do you have any questions or comments?"

You: "No, this is cool!"

Agent: "Thank you! I've recorded your response. Have a great day!"

📞 Call ends
```

### View Results

1. Check "Recent Calls" section on dashboard
2. Click "View Transcript" to see the conversation
3. Click "Play Recording" to hear the audio

## Troubleshooting

### Call doesn't connect

**Check Twilio Console:**
- Go to https://console.twilio.com/debugger
- See detailed error messages

**Common issues:**
- Wrong phone number format (must include +country code)
- Twilio trial account restrictions (can only call verified numbers)
- Wrong credentials in .env

**Solution for trial account:**
- Verify your phone at: https://console.twilio.com/verified-caller-ids
- Or upgrade Twilio account ($20 minimum)

### Webhooks fail

**Check ngrok:**
- Is ngrok still running?
- Does PUBLIC_URL in .env match ngrok URL?
- Did ngrok restart? (URL changes each time on free tier)

**Solution:**
```bash
# Get current ngrok URL
curl http://localhost:4040/api/tunnels

# Update .env with new URL
# Restart containers
docker-compose restart
```

### Dashboard doesn't load

```bash
# Check if containers are running
docker ps

# View logs
docker-compose logs -f app

# Common fix: restart
docker-compose down
docker-compose up
```

### Audio issues

**Verify OpenAI key:**
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_OPENAI_KEY"
```

**Check billing:**
- Go to https://platform.openai.com/account/billing
- Ensure you have credits

## Next Steps

### Call a Friend
1. Use "Personal Message Call"
2. Send them a fun message!
3. See their response in the transcript

### Test a Facility
1. Use "Facility Test Call"
2. Call your office or another number
3. Check if they confirm "everything is good"
4. View PASS/FAIL result

### Customize the Agent
Edit `app/call_scripts.py` to:
- Change what the agent says
- Modify conversation flow
- Add new questions
- Change voice and tone

### Add More Use Cases
- Appointment reminders
- Survey calls
- Customer follow-ups
- Lead qualification

## Costs for Testing

**Free tier limits:**
- Twilio: $15 credit (enough for ~200 test calls)
- OpenAI: Pay as you go (~$0.10 per call)

**First 10 test calls:** ~$1

## Getting Help

**Check logs:**
```bash
docker-compose logs -f
```

**Database issues:**
```bash
# Reset everything
docker-compose down -v
docker-compose up
```

**Still stuck?**
- Check README.md for detailed docs
- Review Twilio debugger
- Verify all credentials in .env

## Success!

You now have a working AI voice agent!

Try making a few test calls and explore the dashboard. The system will record everything and show you detailed transcripts.

Happy calling! 📞
