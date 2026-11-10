"""Pins the full application route surface so the Phase 3 modularization
(moving endpoints into routers) cannot silently drop or rename a route.
Framework routes (/docs, /openapi.json, /redoc) are intentionally excluded.
"""
import main

EXPECTED_ROUTES = {
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/api/actions"),
    ("GET", "/api/actions/{action_id}"),
    ("GET", "/api/calls"),
    ("GET", "/api/calls/{call_id}"),
    ("GET", "/api/calls/{call_id}/analysis"),
    ("GET", "/api/reports/summary"),
    ("GET", "/api/tasks"),
    ("GET", "/api/tasks/{task_id}"),
    ("GET", "/twilio/play-ai-dynamic"),
    ("GET", "/twilio/play-ai-response"),
    ("PATCH", "/api/actions/{action_id}"),
    ("PATCH", "/api/tasks/{task_id}"),
    ("POST", "/api/analyze-all-calls"),
    ("POST", "/api/calls/facility-test"),
    ("POST", "/api/calls/livekit-call"),
    ("POST", "/api/calls/personal-message"),
    ("POST", "/api/calls/recurring"),
    ("POST", "/api/calls/schedule"),
    ("POST", "/api/calls/{call_id}/analyze"),
    ("POST", "/api/calls/{call_id}/cancel"),
    ("POST", "/api/calls/{call_id}/pause"),
    ("POST", "/api/calls/{call_id}/resume"),
    ("POST", "/api/contacts/upload-csv"),
    ("POST", "/api/reports/daily"),
    ("POST", "/api/tasks/assign"),
    ("POST", "/api/tasks/{task_id}/call"),
    ("POST", "/livekit/webhook"),
    ("POST", "/twilio/call-ended"),
    ("POST", "/twilio/call-status"),
    ("POST", "/twilio/no-response"),
    ("POST", "/twilio/play-ai-dynamic"),
    ("POST", "/twilio/play-ai-response"),
    ("POST", "/twilio/process-response"),
}


def _current_routes():
    found = set()
    for r in main.app.routes:
        methods = getattr(r, "methods", None)
        if not methods:
            continue
        for m in methods:
            if m in ("HEAD", "OPTIONS"):
                continue
            found.add((m, r.path))
    return found


def test_all_expected_routes_registered():
    missing = EXPECTED_ROUTES - _current_routes()
    assert not missing, f"routes dropped/renamed: {sorted(missing)}"
