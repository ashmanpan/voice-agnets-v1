"""API-key authentication middleware.

Protects mutating requests (POST/PUT/PATCH/DELETE) under /api/ by requiring a
matching `X-API-Key` header. Fail-closed: if the API_KEY env var is unset,
protected routes are rejected rather than left open.

Webhook endpoints live under /twilio/* and /livekit/* (not /api/), so external
providers that cannot send our key are unaffected.
"""
import hmac
import os
import threading
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# --- Rate limiting (in-memory fixed window, keyed by API key / client host) ---
_rl_lock = threading.Lock()
_rl_hits: dict = defaultdict(list)


def reset_rate_limit() -> None:
    """Clear all recorded hits (used by tests)."""
    with _rl_lock:
        _rl_hits.clear()


def _rl_config():
    return int(os.getenv("CALL_RATE_LIMIT", "10")), float(os.getenv("CALL_RATE_WINDOW", "60"))


def _is_call_trigger(method: str, path: str) -> bool:
    return method == "POST" and (path.startswith("/api/calls/") or path.endswith("/call"))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """429s call-trigger POSTs once a key exceeds CALL_RATE_LIMIT per window."""

    async def dispatch(self, request, call_next):
        if _is_call_trigger(request.method, request.url.path):
            limit, window = _rl_config()
            key = request.headers.get("x-api-key") or (
                request.client.host if request.client else "anonymous"
            )
            now = time.monotonic()
            with _rl_lock:
                hits = _rl_hits[key]
                hits[:] = [t for t in hits if t > now - window]
                if len(hits) >= limit:
                    return JSONResponse(
                        {"detail": "Rate limit exceeded"}, status_code=429
                    )
                hits.append(now)
        return await call_next(request)


def _is_protected(method: str, path: str) -> bool:
    # Protect every method under /api/ — reads expose PII (transcripts,
    # contacts) too. OPTIONS is exempt so CORS preflight works.
    return path.startswith("/api/") and method != "OPTIONS"


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if _is_protected(request.method, request.url.path):
            expected = os.getenv("API_KEY")
            provided = request.headers.get("x-api-key")
            if not expected or not provided or not hmac.compare_digest(provided, expected):
                return JSONResponse(
                    {"detail": "Invalid or missing API key"}, status_code=401
                )
        return await call_next(request)
