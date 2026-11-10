"""API-key authentication middleware.

Protects mutating requests (POST/PUT/PATCH/DELETE) under /api/ by requiring a
matching `X-API-Key` header. Fail-closed: if the API_KEY env var is unset,
protected routes are rejected rather than left open.

Webhook endpoints live under /twilio/* and /livekit/* (not /api/), so external
providers that cannot send our key are unaffected.
"""
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _is_protected(method: str, path: str) -> bool:
    return method in MUTATING_METHODS and path.startswith("/api/")


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if _is_protected(request.method, request.url.path):
            expected = os.getenv("API_KEY")
            provided = request.headers.get("x-api-key")
            if not expected or provided != expected:
                return JSONResponse(
                    {"detail": "Invalid or missing API key"}, status_code=401
                )
        return await call_next(request)
