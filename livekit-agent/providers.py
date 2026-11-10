"""Swappable STT/TTS provider selection for the voice agent.

Pick providers by env var (TTS_PROVIDER / STT_PROVIDER); default to the
current OpenAI stack. An unknown name fails fast with a clear error; a
provider that fails to construct (e.g. a missing key) falls back to the
default so a call is never dropped for a config slip.

Plugin imports are lazy (inside builders) so this module imports without the
heavy livekit plugins installed, which keeps the selection logic unit-testable
offline.
"""
import os

DEFAULT_TTS = "openai"
DEFAULT_STT = "openai"

# Pipeline modes: "cascade" = STT->LLM->TTS (default); "realtime" = a single
# speech-to-speech model (OpenAI Realtime) with no separate STT/TTS.
PIPELINE_MODES = ("cascade", "realtime")


def pipeline_mode(mode=None):
    """Return the configured PIPELINE_MODE, validated. Unknown => ValueError."""
    name = (mode or os.getenv("PIPELINE_MODE", "cascade")).lower()
    if name not in PIPELINE_MODES:
        raise ValueError(
            f"Unknown PIPELINE_MODE '{name}'. Options: {list(PIPELINE_MODES)}"
        )
    return name


def build_realtime_llm():
    """Build the OpenAI Realtime speech-to-speech model (used in realtime mode)."""
    from livekit.plugins import openai
    return openai.realtime.RealtimeModel(
        voice=os.getenv("REALTIME_VOICE", "alloy"),
    )


def _default_tts_builders():
    def openai_tts():
        from livekit.plugins import openai
        return openai.TTS(
            voice=os.getenv("OPENAI_TTS_VOICE", "alloy"),
            speed=float(os.getenv("OPENAI_TTS_SPEED", "1.0")),
        )

    def elevenlabs_tts():
        from livekit.plugins import elevenlabs
        kwargs = {"model": os.getenv("ELEVEN_MODEL", "eleven_flash_v2_5")}
        voice_id = os.getenv("ELEVEN_VOICE_ID")
        if voice_id:
            kwargs["voice_id"] = voice_id
        return elevenlabs.TTS(**kwargs)

    return {"openai": openai_tts, "elevenlabs": elevenlabs_tts}


def _default_stt_builders(language=None):
    def openai_stt():
        from livekit.plugins import openai
        kwargs = {"model": os.getenv("OPENAI_STT_MODEL", "whisper-1")}
        # whisper auto-detects English; pass an explicit hint otherwise.
        if language and language != "en":
            kwargs["language"] = language
        return openai.STT(**kwargs)

    def deepgram_stt():
        from livekit.plugins import deepgram
        kwargs = {"model": os.getenv("DEEPGRAM_STT_MODEL", "nova-2")}
        if language:
            kwargs["language"] = language
        return deepgram.STT(**kwargs)

    return {"openai": openai_stt, "deepgram": deepgram_stt}


def _build(kind, provider, env_var, default, builders):
    name = (provider or os.getenv(env_var, default)).lower()
    if name not in builders:
        raise ValueError(
            f"Unknown {env_var} '{name}'. Options: {sorted(builders)}"
        )
    try:
        return builders[name]()
    except Exception as exc:
        if name != default:
            print(f"⚠️ {kind} provider '{name}' failed ({exc}); falling back to '{default}'")
            return builders[default]()
        raise


def build_tts(provider=None, *, builders=None):
    """Return a TTS instance for TTS_PROVIDER (or the given provider)."""
    return _build("TTS", provider, "TTS_PROVIDER", DEFAULT_TTS, builders or _default_tts_builders())


def build_stt(provider=None, *, language=None, builders=None):
    """Return an STT instance for STT_PROVIDER (or the given provider).

    `language` is an optional per-call hint passed to the default builders.
    """
    return _build("STT", provider, "STT_PROVIDER", DEFAULT_STT, builders or _default_stt_builders(language))
