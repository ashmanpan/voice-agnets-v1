"""Telephony consolidation: LiveKit SIP is primary; the legacy Twilio TwiML
webhooks can be disabled via ENABLE_TWILIO_WEBHOOKS=false."""

TWILIO_WEBHOOK = "/twilio/call-status"


def test_twilio_webhooks_disabled_returns_410(client, monkeypatch):
    monkeypatch.setenv("ENABLE_TWILIO_WEBHOOKS", "false")
    r = client.post(TWILIO_WEBHOOK, data={})
    assert r.status_code == 410


def test_twilio_webhooks_enabled_by_default(client, monkeypatch):
    monkeypatch.delenv("ENABLE_TWILIO_WEBHOOKS", raising=False)
    r = client.post(TWILIO_WEBHOOK, data={})
    assert r.status_code != 410
