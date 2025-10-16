# Voice Agent System

An AI-powered voice agent that makes automated phone calls for personal messages and facility testing. Runs completely in Docker containers on your laptop.

## Features

### Use Case 1: Personal Message Delivery
- Call a friend's number
- Agent says: "Hi, my name is SOS and I want to give you an update: [your message]"
- Records the friend's response
- Saves transcript and audio recording

### Use Case 2: Facility Test Calls
- Call facility number
- Agent identifies as test call
- Asks operator to confirm everything is working
- Records test result (PASS/FAIL)
- Saves transcript and audio

## Architecture

```
┌─────────────────────────────────────┐
│   Docker Containers (Your Laptop)  │
├─────────────────────────────────────┤
│  - FastAPI Application              │
│  - PostgreSQL Database              │
│  - Web Dashboard                    │
└─────────────────────────────────────┘
         │
         ↓ (via ngrok/public URL)
┌─────────────────────────────────────┐
│   External Cloud Services           │
├─────────────────────────────────────┤
│  - Twilio (phone calls)             │
│  - OpenAI Whisper (speech-to-text)  │
│  - OpenAI TTS (text-to-speech)      │
└─────────────────────────────────────┘
```

## Prerequisites

1. **Docker Desktop** installed and running
2. **Twilio Account**
   - Sign up at https://twilio.com
   - Get a phone number (~$1/month)
   - Note your Account SID and Auth Token
3. **OpenAI API Key**
   - Sign up at https://platform.openai.com
   - Add payment method
   - Create API key
4. **ngrok** (for local development)
   - Sign up at https://ngrok.com (free tier is fine)
   - Install ngrok CLI

## Setup Instructions

### Step 1: Clone and Configure

```bash
# Navigate to project directory
cd voice-agents

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Update the following in `.env`:
```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890  # Your Twilio number

OPENAI_API_KEY=your_openai_api_key

PUBLIC_URL=https://your-ngrok-url.ngrok.io  # Will update after starting ngrok
```

### Step 2: Start ngrok

In a separate terminal, start ngrok to expose your local server:

```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** and update `PUBLIC_URL` in your `.env` file:
```env
PUBLIC_URL=https://abc123.ngrok.io
```

### Step 3: Build and Start Docker Containers

```bash
# Build the Docker image
docker-compose build

# Start all services
docker-compose up
```

Wait for:
- Database to initialize
- Application to start
- You should see: "Application startup complete"

### Step 4: Access the Dashboard

Open your browser and go to:
```
http://localhost:8000
```

You should see the Voice Agent Dashboard!

## Making Your First Call

### Personal Message Call

1. Click on "Personal Message Call" tab
2. Fill in:
   - Friend's Name: "John"
   - Phone Number: "+15551234567"
   - Message: "Hey, I'm running late. See you in 15 minutes!"
3. Click "Make Call Now"
4. The system will call the number and deliver your message
5. View the transcript and recording in "Recent Calls"

### Facility Test Call

1. Click on "Facility Test Call" tab
2. Fill in:
   - Facility Name: "Building A Security"
   - Phone Number: "+15559876543"
3. Click "Make Test Call"
4. The system will call and verify the line is working
5. View test result (PASS/FAIL) in "Recent Calls"

## Project Structure

```
voice-agents/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Database models
│   ├── twilio_handler.py       # Twilio integration
│   ├── call_scripts.py         # Call flow scripts
│   ├── speech_services.py      # TTS/STT integration
│   └── static/
│       ├── index.html          # Web dashboard
│       ├── style.css           # Styling
│       └── app.js              # Frontend logic
├── database/
│   └── schema.sql              # Database schema
├── recordings/                 # Call recordings stored here
├── docker-compose.yml          # Docker configuration
├── Dockerfile                  # App container image
├── requirements.txt            # Python dependencies
└── .env                        # Configuration (create from .env.example)
```

## API Endpoints

### Web Dashboard
- `GET /` - Main dashboard

### API Routes
- `POST /api/calls/personal-message` - Create personal message call
- `POST /api/calls/facility-test` - Create facility test call
- `GET /api/calls/{call_id}` - Get call details and transcript

### Twilio Webhooks (called by Twilio)
- `POST /twilio/call-status` - Call status updates
- `POST /twilio/process-response` - Process user responses
- `POST /twilio/call-ended` - Call completion

## Database Schema

### contacts
- Contact information (name, phone number, type)

### calls
- Call records (status, duration, recordings)
- Custom messages for personal calls
- Test results for facility calls

### transcript_segments
- Detailed conversation transcript
- Speaker identification (agent/user)
- Timestamps

## Troubleshooting

### Calls Not Connecting

1. **Check Twilio credentials** in `.env`
2. **Verify Twilio phone number** has voice capabilities
3. **Check ngrok is running** and URL is correct in `.env`
4. **Restart containers** after changing `.env`:
   ```bash
   docker-compose down
   docker-compose up
   ```

### Webhook Errors

1. **Ensure PUBLIC_URL matches ngrok URL**
2. **Check ngrok is still running** (restarts change the URL)
3. **View Twilio debugger**: https://console.twilio.com/debugger

### Database Issues

```bash
# Reset database
docker-compose down -v  # Removes volumes
docker-compose up      # Recreates fresh database
```

### Audio/Speech Issues

1. **Verify OpenAI API key** is valid
2. **Check API credits**: https://platform.openai.com/account/billing
3. **Test TTS/STT separately** using OpenAI playground

## Costs

### Per Call (5 minute average)
- Twilio: ~$0.065
- OpenAI Whisper (STT): ~$0.03
- OpenAI TTS: ~$0.002
- **Total: ~$0.10 per call**

### Monthly Estimates
- **Light use** (100 calls/month): ~$10
- **Medium use** (500 calls/month): ~$50
- **Heavy use** (2000 calls/month): ~$200

Plus:
- Twilio phone number: $1-2/month
- Server: Free (runs on your laptop)

## Development

### View Logs

```bash
# All services
docker-compose logs -f

# Just the app
docker-compose logs -f app

# Database
docker-compose logs -f db
```

### Access Database

```bash
docker exec -it voice-agents-db-1 psql -U voiceagent -d voiceagent
```

### Run Commands in Container

```bash
docker exec -it voice-agents-app-1 bash
```

## Customization

### Modify Call Scripts

Edit `app/call_scripts.py` to change:
- Agent's voice and tone
- Conversation flow
- Wait times
- Response handling

### Change Voice

In `call_scripts.py`, update the `voice` field:
- Available voices: alloy, echo, fable, onyx, nova, shimmer
- Or use Twilio voices (Polly.Joanna, Polly.Matthew, etc.)

### Add New Use Cases

1. Create new script in `call_scripts.py`
2. Add form in `static/index.html`
3. Add API endpoint in `main.py`
4. Add form handler in `static/app.js`

## Security Notes

- **.env file contains secrets** - never commit to git
- **ngrok URLs are public** - only for development
- **Production**: Deploy to cloud with HTTPS
- **Phone numbers**: Validate before calling
- **Rate limiting**: Add to prevent abuse

## Next Steps

### V2 Features to Add
- Database integrations
- CRM sync
- Multi-language support (Hindi, Marathi)
- Call scheduling
- Campaign management
- A/B testing scripts
- Self-hosted STT/TTS (cost reduction)

## Support

- Check logs: `docker-compose logs -f`
- Twilio debugger: https://console.twilio.com/debugger
- OpenAI status: https://status.openai.com

## License

MIT License - Use freely for your projects!
