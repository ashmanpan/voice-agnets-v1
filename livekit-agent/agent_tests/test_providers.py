"""Offline tests for the TTS/STT provider abstraction: default selection,
env override, unknown-provider failure, and fallback. Builders are injected
so no real livekit plugin / network is needed."""
import pytest

import providers


def _tts_builders():
    return {"openai": lambda: "OPENAI_TTS", "elevenlabs": lambda: "ELEVEN_TTS"}


def test_default_tts_is_openai(monkeypatch):
    monkeypatch.delenv("TTS_PROVIDER", raising=False)
    assert providers.build_tts(builders=_tts_builders()) == "OPENAI_TTS"


def test_tts_provider_env_selects_elevenlabs(monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "elevenlabs")
    assert providers.build_tts(builders=_tts_builders()) == "ELEVEN_TTS"


def test_unknown_tts_provider_raises(monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "bogus")
    with pytest.raises(ValueError):
        providers.build_tts(builders=_tts_builders())


def test_tts_falls_back_to_default_on_error(monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "elevenlabs")

    def boom():
        raise RuntimeError("missing ELEVEN_API_KEY")

    builders = {"openai": lambda: "OPENAI_TTS", "elevenlabs": boom}
    assert providers.build_tts(builders=builders) == "OPENAI_TTS"


def _stt_builders():
    return {"openai": lambda: "OPENAI_STT", "deepgram": lambda: "DEEPGRAM_STT"}


def test_default_stt_is_openai(monkeypatch):
    monkeypatch.delenv("STT_PROVIDER", raising=False)
    assert providers.build_stt(builders=_stt_builders()) == "OPENAI_STT"


def test_stt_provider_env_selects_deepgram(monkeypatch):
    monkeypatch.setenv("STT_PROVIDER", "deepgram")
    assert providers.build_stt(builders=_stt_builders()) == "DEEPGRAM_STT"


def test_default_pipeline_mode_is_cascade(monkeypatch):
    monkeypatch.delenv("PIPELINE_MODE", raising=False)
    assert providers.pipeline_mode() == "cascade"


def test_pipeline_mode_env_selects_realtime(monkeypatch):
    monkeypatch.setenv("PIPELINE_MODE", "realtime")
    assert providers.pipeline_mode() == "realtime"


def test_unknown_pipeline_mode_raises(monkeypatch):
    monkeypatch.setenv("PIPELINE_MODE", "bogus")
    with pytest.raises(ValueError):
        providers.pipeline_mode()
