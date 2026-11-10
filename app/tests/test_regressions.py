"""Regressions found in the Phase 3 router extraction (final review)."""
import models


def test_assign_with_scheduled_time_invokes_scheduler(client, db_session, monkeypatch):
    """The router extraction dropped `schedule_one_time_call`'s import, so the
    scheduled path raised NameError (swallowed -> 500, call never scheduled).
    monkeypatch(raising=True) also asserts the name now exists in the module."""
    import routers.tasks as tasks_router

    recorded = []
    monkeypatch.setattr(
        tasks_router, "schedule_one_time_call", lambda *a, **k: recorded.append(a)
    )

    contact = models.Contact(
        name="Sched", phone_number="+15550003333", contact_type="facility"
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    r = client.post("/api/tasks/assign", data={
        "contact_id": contact.id,
        "title": "Call back",
        "description": "please call back",
        "scheduled_time": "2030-01-01T10:00:00",
    })

    assert r.status_code == 200
    assert r.json()["success"] is True
    assert len(recorded) == 1  # the scheduler was actually invoked


def test_webhooks_module_imports_os_at_module_level():
    """The Twilio TwiML handlers use os.getenv('PUBLIC_URL'); extraction left
    `import os` only function-local, so other handlers NameError'd mid-call."""
    import routers.webhooks as wh
    assert hasattr(wh, "os")
