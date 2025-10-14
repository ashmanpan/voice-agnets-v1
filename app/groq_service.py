"""
Groq AI integration for ultra-low latency conversational AI
Uses Groq's fast inference for real-time voice conversations
"""
import os
from groq import Groq

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Best models for voice agents (ranked by speed and quality)
GROQ_MODELS = {
    "fastest": "llama-3.3-70b-versatile",      # Ultra-fast, great quality
    "balanced": "llama-3.1-70b-versatile",     # Fast, excellent quality
    "lightweight": "llama-3.1-8b-instant",     # Fastest, good for simple tasks
}


def generate_conversation_response(
    conversation_history: list,
    call_type: str = None,
    model: str = "fastest",
    system_prompt: str = None
) -> str:
    """
    Generate AI response for conversation using Groq

    Args:
        conversation_history: List of {"role": "user/assistant", "content": "text"}
        call_type: "personal_message" or "facility_test" (optional if system_prompt provided)
        model: "fastest", "balanced", or "lightweight"
        system_prompt: Custom system prompt (optional, overrides call_type prompts)

    Returns:
        AI generated response text
    """

    # System prompts for different call types
    system_prompts = {
        "personal_message": """You are SOS's voice agent assistant.
        You are helping deliver personal messages to friends.
        Be friendly, concise, and natural.
        Keep responses under 2 sentences.
        You've already delivered the main message, now just handle follow-up questions briefly.""",

        "facility_test": """You are a professional test call agent.
        Your job is to verify phone lines are working properly.
        Be polite, clear, and efficient.
        Listen for positive confirmations (yes, good, working) or negative (no, problem, issue).
        Keep responses under 2 sentences."""
    }

    # Use custom system prompt if provided, otherwise use call_type default
    if system_prompt is None:
        system_prompt = system_prompts.get(call_type, system_prompts["personal_message"])

    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt}
    ] + conversation_history

    try:
        # Call Groq API with selected model
        completion = groq_client.chat.completions.create(
            model=GROQ_MODELS[model],
            messages=messages,
            temperature=0.7,
            max_tokens=100,  # Keep responses short for voice
            top_p=0.9,
            stream=False
        )

        response = completion.choices[0].message.content
        return response.strip()

    except Exception as e:
        print(f"Groq API Error: {e}")
        # Fallback response
        return "Thank you for your response."


def analyze_user_response(
    user_text: str,
    keywords_positive: list,
    keywords_negative: list
) -> str:
    """
    Use Groq to analyze user response sentiment with AI
    More accurate than keyword matching

    Args:
        user_text: User's spoken response
        keywords_positive: Hint words for positive
        keywords_negative: Hint words for negative

    Returns:
        'positive', 'negative', or 'neutral'
    """

    prompt = f"""Analyze this response and determine if it's positive, negative, or neutral.

User said: "{user_text}"

Positive indicators: {', '.join(keywords_positive)}
Negative indicators: {', '.join(keywords_negative)}

Respond with only ONE word: positive, negative, or neutral"""

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODELS["lightweight"],  # Fast model for simple task
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=10
        )

        result = completion.choices[0].message.content.strip().lower()

        if "positive" in result:
            return "positive"
        elif "negative" in result:
            return "negative"
        else:
            return "neutral"

    except Exception as e:
        print(f"Groq sentiment analysis error: {e}")
        # Fallback to simple keyword matching
        from speech_services import analyze_sentiment
        return analyze_sentiment(user_text, keywords_positive, keywords_negative)


def generate_dynamic_response(
    user_question: str,
    context: dict
) -> str:
    """
    Generate dynamic responses to unexpected user questions

    Args:
        user_question: What the user asked
        context: Call context (name, message, etc.)

    Returns:
        Natural response
    """

    prompt = f"""You are a voice agent delivering a message. The user just asked a question.

Context:
- You called {context.get('name', 'someone')}
- You delivered this message: "{context.get('message', '')}"

User asked: "{user_question}"

Respond naturally and helpfully, but keep it very brief (1-2 sentences max) since this is a phone call."""

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODELS["fastest"],
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=80
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"Groq dynamic response error: {e}")
        return "I've noted your question. Thank you!"


# Performance comparison (approximate inference times)
"""
Groq vs OpenAI latency:

Model                          | Time to First Token | Tokens/sec
-------------------------------|---------------------|------------
Groq llama-3.3-70b            | ~50ms               | ~300
Groq llama-3.1-70b            | ~60ms               | ~280
Groq llama-3.1-8b             | ~30ms               | ~500
OpenAI GPT-4                  | ~800ms              | ~40
OpenAI GPT-3.5-turbo          | ~400ms              | ~80

For voice agents, Groq is 6-10x faster! This means:
- More natural conversation flow
- Less awkward pauses
- Better user experience
"""
