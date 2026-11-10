"""Characterization tests pinning the existing calls API behavior, so later
refactors (Phase 3) can't silently change it. The detail endpoint already
exists, so its test passes on first run by design — it records current
behavior rather than driving new code. The missing calls-list endpoint is
recorded as a strict xfail that will flip to a failure once Phase 3 adds it.
"""
from datetime import datetime

import pytest

import models


def test_call_detail_returns_call_with_transcript(client, db_session):
    contact = models.Contact(
        name="Parity User", phone_number="+15550001111", contact_type="facility"
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    call = models.Call(
        contact_id=contact.id, call_type="facility_test", status="completed"
    )
    db_session.add(call)
    db_session.commit()
    db_session.refresh(call)

    db_session.add_all([
        models.TranscriptSegment(
            call_id=call.id, speaker="agent", text="Hello",
            timestamp=datetime(2026, 1, 1, 0, 0, 0), sequence_number=1,
        ),
        models.TranscriptSegment(
            call_id=call.id, speaker="user", text="Hi there",
            timestamp=datetime(2026, 1, 1, 0, 0, 5), sequence_number=2,
        ),
    ])
    db_session.commit()

    r = client.get(f"/api/calls/{call.id}")

    assert r.status_code == 200
    body = r.json()
    assert body["call"]["id"] == call.id
    assert body["call"]["status"] == "completed"
    assert body["contact"]["name"] == "Parity User"
    assert [seg["text"] for seg in body["transcript"]] == ["Hello", "Hi there"]


@pytest.mark.xfail(
    strict=True,
    reason="audit gap: no GET /api/calls list endpoint yet (added in Phase 3)",
)
def test_calls_list_endpoint_exists(client):
    r = client.get("/api/calls")
    assert r.status_code == 200
