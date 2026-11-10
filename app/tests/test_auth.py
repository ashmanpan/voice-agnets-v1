"""API-key enforcement on mutating /api routes (Review Focus #1)."""

CALL_TRIGGER = "/api/calls/livekit-call"
CALL_BODY = {"name": "Test User", "phone": "+15551230000"}


def test_mutating_api_requires_key(unauthenticated_client, dispatch_records):
    r = unauthenticated_client.post(CALL_TRIGGER, data=CALL_BODY)
    assert r.status_code == 401
    assert len(dispatch_records) == 0  # rejected before any dispatch


def test_mutating_api_rejects_wrong_key(client, dispatch_records):
    r = client.post(CALL_TRIGGER, data=CALL_BODY, headers={"x-api-key": "wrong"})
    assert r.status_code == 401
    assert len(dispatch_records) == 0


def test_authenticated_call_still_dispatches(client, dispatch_records):
    r = client.post(CALL_TRIGGER, data=CALL_BODY)
    assert r.status_code == 200
    assert len(dispatch_records) == 1
