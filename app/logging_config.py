"""Structured application logging. Call configure_logging() once at startup.

Replaces ad-hoc print() with a consistent, leveled format on stdout. Level is
taken from LOG_LEVEL (default INFO). Idempotent — safe to call more than once.
"""
import logging
import os
import sys

_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_configured = False


def configure_logging(level=None):
    """Configure the root logger. Returns it. Idempotent (no duplicate handlers)."""
    global _configured
    lvl = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    root = logging.getLogger()
    root.setLevel(lvl)
    if not _configured:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(handler)
        _configured = True
    return root
