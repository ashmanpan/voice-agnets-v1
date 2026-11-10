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

# --- Rate limiting (in-memory fixed window) ---
_rl_lock = threading.Lock()
_rl_hits: dict = defaultdict(list)
_RL_MAX_BUCKETS = 4096  # hard cap so buckets can't grow without bound

# Costly POST routes outside the /api/calls/ prefix (exact paths).
_CALL_TRIGGER_PATHS = frozenset({
    "/api/tasks/assign",
    "/api/analyze-all-calls",
    "/api/reports/daily",
})


def reset_rate_limit() -> None:
    """Clear all recorded hits (used by tests)."""
    with _rl_lock:
        _rl_hits.clear()


def _rl_config():
    return int(os.getenv("CALL_RATE_LIMIT", "10")), float(os.getenv("CALL_RATE_WINDOW", "60"))


def _is_call_trigger(method: str, path: str) -> bool:
    if method != "POST":
        return False
    # Safer prefix default: every POST under /api/calls/ (place/schedule/
    # analyze/resume/cancel/pause, incl. dynamic {id} subpaths), plus explicit
    # costly routes elsewhere and the per-task call endpoint /api/tasks/{id}/call.
    return (
        path.startswith("/api/calls/")
        or path in _CALL_TRIGGER_PATHS
        or (path.startswith("/api/tasks/") and path.endswith("/call"))
    )


def _rl_bucket_key(request) -> str:
    """Bucket authenticated requests under a fixed id (an attacker cannot
    create unbounded buckets via the X-API-Key header); otherwise key by the
    client IP."""
    expected = os.getenv("API_KEY")
    provided = request.headers.get("x-api-key")
    if expected and provided and hmac.compare_digest(provided, expected):
        return "authenticated"
    return request.client.host if request.client else "anonymous"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """429s call-trigger POSTs once a bucket exceeds CALL_RATE_LIMIT per window."""

    async def dispatch(self, request, call_next):
        if _is_call_trigger(request.method, request.url.path):
            limit, window = _rl_config()
            key = _rl_bucket_key(request)
            now = time.monotonic()
            with _rl_lock:
                hits = _rl_hits[key]
                hits[:] = [t for t in hits if t > now - window]
                if len(hits) >= limit:
                    return JSONResponse(
                        {"detail": "Rate limit exceeded"}, status_code=429
                    )
                hits.append(now)
                self._evict_if_needed()
        return await call_next(request)

    @staticmethod
    def _evict_if_needed():
        """Drop empty buckets, then oldest arbitrary buckets, to stay bounded."""
        if len(_rl_hits) <= _RL_MAX_BUCKETS:
            return
        for k in [k for k, v in _rl_hits.items() if not v]:
            del _rl_hits[k]
        while len(_rl_hits) > _RL_MAX_BUCKETS:
            _rl_hits.pop(next(iter(_rl_hits)))


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
