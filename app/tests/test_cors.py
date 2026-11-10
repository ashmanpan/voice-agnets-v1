"""CORS scoped to the frontend origin (Review Focus #2)."""

ALLOWED_ORIGIN = "http://localhost:5173"
OTHER_ORIGIN = "https://evil.example.com"
PREFLIGHT_HEADERS = {"Access-Control-Request-Method": "POST"}


def test_preflight_allows_frontend_origin(client):
    r = client.options(
        "/api/calls/livekit-call",
        headers={"Origin": ALLOWED_ORIGIN, **PREFLIGHT_HEADERS},
    )
    assert r.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


def test_preflight_denies_other_origin(client):
    r = client.options(
        "/api/calls/livekit-call",
        headers={"Origin": OTHER_ORIGIN, **PREFLIGHT_HEADERS},
    )
    assert r.headers.get("access-control-allow-origin") != OTHER_ORIGIN
