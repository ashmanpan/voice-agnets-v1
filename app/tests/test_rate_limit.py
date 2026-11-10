"""Rate limiting on call-trigger endpoints (Review Focus #3)."""
import security

CALL_TRIGGER = "/api/calls/livekit-call"
CALL_BODY = {"name": "Test User", "phone": "+15551230000"}


def test_call_trigger_blocks_past_limit(client, dispatch_records, monkeypatch):
    monkeypatch.setenv("CALL_RATE_LIMIT", "3")
    security.reset_rate_limit()

    for _ in range(3):
        assert client.post(CALL_TRIGGER, data=CALL_BODY).status_code == 200

    blocked = client.post(CALL_TRIGGER, data=CALL_BODY)
    assert blocked.status_code == 429
    assert len(dispatch_records) == 3  # the blocked request never dispatched


def test_task_assign_is_rate_limited(client, monkeypatch):
    """Call-placing/costly routes beyond /api/calls/ are covered too
    (security review: incomplete coverage)."""
    monkeypatch.setenv("CALL_RATE_LIMIT", "2")
    security.reset_rate_limit()

    for _ in range(2):
        client.post("/api/tasks/assign", json={})
    blocked = client.post("/api/tasks/assign", json={})
    assert blocked.status_code == 429
