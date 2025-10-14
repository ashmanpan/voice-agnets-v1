# Groq Integration for Ultra-Low Latency Voice Calls

## Why Groq for Voice Agents?

Groq provides **6-10x faster** inference than traditional LLMs, making it perfect for real-time voice conversations.

### Speed Comparison

| Model | Time to First Token | Tokens/sec | Best For |
|-------|---------------------|-----------|----------|
| **Groq Llama 3.3 70B** | ~50ms | ~300 | Voice agents (RECOMMENDED) |
| **Groq Llama 3.1 70B** | ~60ms | ~280 | Complex conversations |
| **Groq Llama 3.1 8B** | ~30ms | ~500 | Simple, ultra-fast responses |
| OpenAI GPT-4 | ~800ms | ~40 | Not recommended for voice |
| OpenAI GPT-3.5 | ~400ms | ~80 | Acceptable but slow |

### What This Means for Your Voice Agent

**Without Groq (OpenAI GPT-3.5):**
```
User: "Can I reschedule?"
[400ms pause] ← Feels awkward
Agent: "Of course! When works better for you?"
```

**With Groq (Llama 3.3 70B):**
```
User: "Can I reschedule?"
[50ms pause] ← Feels natural
Agent: "Of course! When works better for you?"
```

## Setup

### 1. Your API Key

Your Groq API key is already in `.env.example`:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 2. Install Groq Package

Already added to `requirements.txt`:
```
groq==0.4.1
```

When you run `docker-compose build`, it will install automatically.

### 3. How It's Used

The `groq_service.py` module provides three main functions:

#### a) Generate Conversation Responses
```python
from groq_service import generate_conversation_response

# For dynamic, intelligent responses
conversation_history = [
    {"role": "user", "content": "Can you call me back later?"},
]

response = generate_conversation_response(
    conversation_history,
    call_type="personal_message",
    model="fastest"  # Uses Llama 3.3 70B
)
# Returns: "Of course! What time works best for you?"
```

#### b) Analyze User Sentiment
```python
from groq_service import analyze_user_response

# Smarter than keyword matching
sentiment = analyze_user_response(
    user_text="Yeah, everything seems to be working fine",
    keywords_positive=["yes", "good", "working"],
    keywords_negative=["no", "problem", "issue"]
)
# Returns: "positive"
```

#### c) Handle Unexpected Questions
```python
from groq_service import generate_dynamic_response

# When user asks something unexpected
response = generate_dynamic_response(
    user_question="Who are you again?",
    context={
        "name": "John",
        "message": "Meeting moved to 3pm"
    }
)
# Returns: "I'm calling on behalf of SOS to let you know the meeting moved to 3pm."
```

## Available Models

### 1. llama-3.3-70b-versatile (fastest) ⚡ **RECOMMENDED**
- **Speed**: 50ms first token, 300 tokens/sec
- **Quality**: Excellent, comparable to GPT-4
- **Use**: Default for all voice conversations
- **Cost**: ~$0.59 per 1M tokens

### 2. llama-3.1-70b-versatile (balanced)
- **Speed**: 60ms first token, 280 tokens/sec
- **Quality**: Excellent
- **Use**: When you need slightly more thoughtful responses
- **Cost**: ~$0.59 per 1M tokens

### 3. llama-3.1-8b-instant (lightweight) ⚡⚡⚡
- **Speed**: 30ms first token, 500 tokens/sec
- **Quality**: Good for simple tasks
- **Use**: Sentiment analysis, simple classifications
- **Cost**: ~$0.05 per 1M tokens

## Cost Comparison

### Per Voice Call (5 minutes)

**Current Setup (OpenAI only):**
- Twilio: $0.065
- Whisper STT: $0.03
- OpenAI TTS: $0.002
- GPT-3.5 conversation: $0.003
- **Total: $0.10 per call**

**With Groq:**
- Twilio: $0.065
- Whisper STT: $0.03
- OpenAI TTS: $0.002
- **Groq conversation: $0.0001** ← 30x cheaper!
- **Total: $0.097 per call**

Not much cheaper, but **MUCH faster** = better user experience!

## When to Use Groq

### ✅ Use Groq For:
- Real-time conversation responses
- Handling unexpected user questions
- Sentiment analysis
- Dynamic conversation flow
- Any AI logic during the call

### ❌ Don't Use Groq For:
- Speech-to-Text (use OpenAI Whisper)
- Text-to-Speech (use OpenAI TTS or Google TTS)
- Long-form content generation
- Code generation

## Integration Examples

### Example 1: Smart Personal Message Call

Instead of rigid scripts, let Groq handle follow-up:

```python
# In call_scripts.py
{
    "id": "handle_followup",
    "use_groq": True,  # Enable dynamic responses
    "agent_says": None,  # Groq will generate this
    "wait_for_response": True
}
```

**Conversation:**
```
Agent: "Hi! My name is SOS. I wanted to let you know the meeting moved to 3pm."
User: "Wait, which meeting?"
Agent: [Groq generates] "The team meeting that was scheduled for 2pm today has been moved to 3pm."
User: "Oh okay, thanks. Can you send me a calendar invite?"
Agent: [Groq generates] "I've noted that. Someone will send you a calendar invite shortly."
```

### Example 2: Intelligent Facility Test

Let Groq understand context:

```python
# User says something ambiguous
User: "Well, the phones work but the internet is down"

# Groq analyzes:
sentiment = analyze_user_response(
    user_text="Well, the phones work but the internet is down",
    keywords_positive=["work", "fine"],
    keywords_negative=["down", "problem"]
)
# Returns: "negative" ← Correctly identifies issue despite mixed message

# Then generates appropriate response:
response = generate_dynamic_response(
    user_question="Well, the phones work but the internet is down",
    context={"call_type": "facility_test"}
)
# Returns: "I understand the phone line is working but there's an internet issue. I'll make a note of that for follow-up."
```

## Advanced Configuration

### Custom System Prompts

Edit `groq_service.py` to customize how the AI behaves:

```python
system_prompts = {
    "personal_message": """You are SOS's voice agent assistant.
    You are helping deliver personal messages to friends.
    Be friendly, concise, and natural.
    Keep responses under 2 sentences.
    Always be helpful and polite.""",

    "facility_test": """You are a professional test call agent.
    Your job is to verify phone lines are working properly.
    Be polite, clear, and efficient.
    Listen carefully and categorize issues accurately.
    Keep responses under 2 sentences."""
}
```

### Temperature Settings

Control creativity vs consistency:

```python
# More creative (good for casual conversations)
temperature=0.9

# Balanced (default)
temperature=0.7

# More consistent (good for professional calls)
temperature=0.5
```

### Max Tokens

Control response length:

```python
# Very brief (voice agents)
max_tokens=50

# Default
max_tokens=100

# Longer responses (if needed)
max_tokens=200
```

## Testing Groq

### Test the Integration

```python
# Test file: test_groq.py
from groq_service import generate_conversation_response

conversation = [
    {"role": "user", "content": "Can I get a callback later?"}
]

response = generate_conversation_response(
    conversation,
    call_type="personal_message",
    model="fastest"
)

print(f"Groq response: {response}")
# Should respond naturally in <100ms
```

### Run the Test

```bash
docker exec -it voice-agents-app-1 python test_groq.py
```

## Monitoring & Debugging

### Check Groq API Status
- Dashboard: https://console.groq.com
- API Status: https://status.groq.com

### View Response Times

Add logging to `groq_service.py`:

```python
import time

start = time.time()
completion = groq_client.chat.completions.create(...)
latency = (time.time() - start) * 1000  # Convert to ms

print(f"Groq latency: {latency:.0f}ms")
```

### Common Errors

**Rate Limit Error:**
```
Error: Rate limit exceeded
```
**Solution**: Groq free tier has limits. Upgrade at console.groq.com

**API Key Error:**
```
Error: Invalid API key
```
**Solution**: Check GROQ_API_KEY in .env file

## Best Practices

### 1. Use the Right Model
- **Conversations**: llama-3.3-70b-versatile
- **Sentiment**: llama-3.1-8b-instant
- **Complex logic**: llama-3.1-70b-versatile

### 2. Keep Prompts Concise
```python
# Good
"Respond to this user question briefly: {question}"

# Bad
"You are an advanced AI assistant with deep knowledge of..."
```

### 3. Set Response Limits
```python
max_tokens=100  # Perfect for voice
max_tokens=50   # For very brief responses
```

### 4. Cache Common Responses
```python
# For frequently asked questions
FAQs = {
    "who are you": "I'm calling on behalf of SOS",
    "why are you calling": "I'm delivering a message for you"
}
```

## Migration from OpenAI GPT

If you're currently using OpenAI GPT-3.5/4:

**Before:**
```python
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[...]
)
```

**After:**
```python
from groq_service import generate_conversation_response
response = generate_conversation_response(
    conversation_history=[...],
    call_type="personal_message"
)
```

That's it! Drop-in replacement with 10x faster responses.

## Next Steps

1. **Test it**: Make a call and notice the faster responses
2. **Customize**: Edit system prompts in `groq_service.py`
3. **Monitor**: Check console.groq.com for usage stats
4. **Optimize**: Fine-tune temperature and max_tokens

## Support

- Groq Documentation: https://console.groq.com/docs
- API Reference: https://console.groq.com/docs/api-reference
- Community: https://discord.gg/groq

Your voice agent is now powered by one of the fastest AI inference engines available! 🚀
