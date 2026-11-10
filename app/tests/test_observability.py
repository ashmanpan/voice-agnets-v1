"""Observability helpers must be safe no-ops when Langfuse isn't configured."""
import observability


def test_langfuse_none_when_unconfigured(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    assert observability.get_langfuse() is None


def test_traced_is_noop_without_langfuse(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    # Must not raise and must yield cleanly even with no backend.
    with observability.traced("some-op", call_id=1) as span:
        assert span is None
