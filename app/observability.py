"""Optional Langfuse tracing, env-gated and fully no-op when unconfigured.

Enable by setting LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY (and optionally
LANGFUSE_HOST). Without them, get_langfuse() returns None and `traced(...)` is
a harmless context manager — so instrumentation never breaks a request and the
langfuse package need not be installed.
"""
import os
from contextlib import contextmanager


def get_langfuse():
    """Return a Langfuse client if configured and importable, else None."""
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        return None
    try:
        from langfuse import Langfuse
        return Langfuse()
    except Exception:
        return None


@contextmanager
def traced(name, **metadata):
    """Trace a block in Langfuse when configured; otherwise a no-op.

    Yields the span (or None). Never raises from tracing itself.
    """
    client = get_langfuse()
    if client is None:
        yield None
        return

    span = None
    try:
        span = client.trace(name=name, metadata=metadata)
    except Exception:
        span = None
    try:
        yield span
    finally:
        try:
            flush = getattr(client, "flush", None)
            if flush:
                flush()
        except Exception:
            pass
