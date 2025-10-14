"""
Speech services for TTS (Text-to-Speech) and STT (Speech-to-Text)
"""
import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def text_to_speech(text: str, voice: str = "alloy") -> bytes:
    """
    Convert text to speech using OpenAI TTS

    Args:
        text: Text to convert to speech
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)

    Returns:
        Audio bytes in MP3 format
    """
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        return response.content
    except Exception as e:
        print(f"TTS Error: {e}")
        raise


async def speech_to_text(audio_url: str) -> str:
    """
    Convert speech to text using OpenAI Whisper

    Args:
        audio_url: URL or path to audio file

    Returns:
        Transcribed text
    """
    try:
        # Download audio file if it's a URL
        import requests
        if audio_url.startswith("http"):
            response = requests.get(audio_url)
            audio_file = response.content

            # Save temporarily
            temp_file = "/tmp/audio_temp.wav"
            with open(temp_file, "wb") as f:
                f.write(audio_file)
        else:
            temp_file = audio_url

        # Transcribe
        with open(temp_file, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="text"
            )

        return transcript
    except Exception as e:
        print(f"STT Error: {e}")
        return ""


def analyze_sentiment(text: str, keywords_positive: list, keywords_negative: list) -> str:
    """
    Simple keyword-based sentiment analysis

    Args:
        text: Text to analyze
        keywords_positive: List of positive keywords
        keywords_negative: List of negative keywords

    Returns:
        'positive', 'negative', or 'neutral'
    """
    text_lower = text.lower()

    # Check for positive keywords
    for keyword in keywords_positive:
        if keyword.lower() in text_lower:
            return "positive"

    # Check for negative keywords
    for keyword in keywords_negative:
        if keyword.lower() in text_lower:
            return "negative"

    return "neutral"
