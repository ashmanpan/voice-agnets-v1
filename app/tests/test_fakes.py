def test_call_trigger_uses_fake_dispatch(client, dispatch_records):
    """Posting to the LiveKit call-trigger endpoint records exactly one
    agent dispatch through the fake and makes zero real network calls."""
    r = client.post(
        "/api/calls/livekit-call",
        data={"name": "Test User", "phone": "+15551230000"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["dispatch_id"] == "fake-dispatch-id"
    assert len(dispatch_records) == 1
