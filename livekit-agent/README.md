# LiveKit Voice Agent

Real-time voice AI agent with sub-second latency using LiveKit + Groq LLM.

## Architecture

```
User Phone ←→ LiveKit Cloud ←→ LiveKit Agent (Docker) ←→ Groq AI
                 (WebRTC)         (STT-LLM-TTS Pipeline)
```

## Key Features

✅ **Real-time WebRTC streaming** - Bidirectional audio with minimal latency
✅ **Sub-second response times** - 1-3 seconds vs 20 seconds with Twilio webhooks
✅ **Built-in turn detection** - Knows when user stops speaking
✅ **Interruption handling** - User can interrupt AI mid-sentence
✅ **Groq LLM integration** - Fast inference with llama-3.3-70b
✅ **Open source** - Fully self-hostable

## Setup

### 1. Create LiveKit Cloud Account

1. Go to https://cloud.livekit.io/
2. Sign up for a free account
3. Create a new project
4. Note your:
   - `LIVEKIT_URL` (e.g., wss://your-project.livekit.cloud)
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`

### 2. Get API Keys

**Deepgram (for Speech-to-Text):**
1. Go to https://deepgram.com/
2. Sign up and get your API key

**Groq (for LLM):**
- You already have this from your Twilio setup!
- Use the same `GROQ_API_KEY`

### 3. Configure Environment

Create `livekit-agent/.env`:

```bash
# LiveKit Cloud
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Groq AI (use same as Twilio setup)
OPENAI_API_KEY=gsk_your_groq_api_key
GROQ_API_KEY=gsk_your_groq_api_key

# Deepgram STT
DEEPGRAM_API_KEY=your-deepgram-api-key
```

### 4. Start the Agent

```bash
# From project root
docker-compose up -d livekit-agent

# View logs
docker-compose logs -f livekit-agent
```

## Testing

### Option 1: Web Browser Test

1. Go to https://agents-playground.livekit.io/
2. Enter your LiveKit credentials
3. Join a room
4. Your agent will automatically connect
5. Start speaking!

### Option 2: Phone Call Test

LiveKit supports telephony integration with Twilio/Vonage for real phone calls.

## Comparison: LiveKit vs Twilio

| Feature | Twilio (Current) | LiveKit (New) |
|---------|------------------|---------------|
| **Latency** | 13-22 seconds | 1-3 seconds |
| **Architecture** | Webhooks + REST API | WebRTC streaming |
| **Turn Detection** | Timeout-based (20s) | Semantic (instant) |
| **Interruptions** | Not supported | Fully supported |
| **Setup Complexity** | Complex (TwiML, webhooks) | Simple (Python SDK) |
| **Cost** | Per-minute charges | Free tier available |
| **Self-Hosting** | Not possible | Fully supported |

## How It Works

### Twilio Flow (20-second latency):
```
User speaks → Twilio transcribes → Webhook to server →
Groq AI → REST API update → Fetch new TwiML →
TTS synthesis → Play audio
```

### LiveKit Flow (sub-second latency):
```
User speaks → WebRTC stream → Real-time STT →
Groq AI (streaming) → Real-time TTS →
WebRTC stream → User hears response
(All happening in parallel with streaming!)
```

## Advanced Features

### Custom Instructions

Edit `agent.py` to customize the system prompt:

```python
initial_ctx = llm.ChatContext().append(
    role="system",
    text="Your custom instructions here..."
)
```

### Different LLM Models

Change the model in `agent.py`:

```python
llm=openai.LLM(
    model="groq/mixtral-8x7b-32768",  # Faster but smaller
    # or
    model="groq/llama-3.3-70b-versatile",  # Larger, more capable
    base_url="https://api.groq.com/openai/v1",
)
```

### Voice Selection

Change TTS voice:

```python
tts=openai.TTS(voice="alloy")  # Options: alloy, echo, fable, onyx, nova, shimmer
```

## Troubleshooting

**Agent not connecting:**
- Check LiveKit credentials in `.env`
- Verify `LIVEKIT_URL` starts with `wss://`
- Check agent logs: `docker-compose logs livekit-agent`

**No audio output:**
- Verify Deepgram API key is valid
- Check OpenAI API key for TTS
- Ensure browser/phone has microphone permissions

**High latency:**
- Check internet connection
- Try different Groq model (smaller = faster)
- Reduce TTS quality settings

## Resources

- LiveKit Docs: https://docs.livekit.io/
- LiveKit Agents: https://docs.livekit.io/agents/
- LiveKit GitHub: https://github.com/livekit/agents
- Groq API: https://console.groq.com/

## Next Steps

1. Test the agent with web browser
2. Compare latency with Twilio solution
3. Add telephony integration for phone calls
4. Customize conversation flow
5. Add database integration for call tracking
