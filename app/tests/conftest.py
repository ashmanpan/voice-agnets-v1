"""Shared pytest fixtures: an offline FastAPI test client backed by a
disposable in-memory SQLite database. No real provider/network calls.

The app module (`main`) has two import-time requirements this file satisfies
before importing it:
  1. It mounts StaticFiles(directory="static") and reads templates from
     "static" relative to the CWD -> we chdir into the app directory.
  2. speech_services instantiates an OpenAI client at import -> we set dummy
     provider keys so import never needs real credentials.
The app's startup handler starts a scheduler (which would touch Postgres),
so the `client` fixture uses TestClient WITHOUT its lifespan context to avoid
triggering startup/shutdown events.
"""
import os
import sys

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Dummy credentials so import-time client construction never needs real keys.
# (speech_services.py and twilio_handler.py build provider clients at import.)
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("DEEPGRAM_API_KEY", "test-deepgram-key")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "AC" + "0" * 32)
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-twilio-token")
os.environ.setdefault("DATABASE_URL", "sqlite://")

TEST_API_KEY = "test-secret-key"
os.environ.setdefault("API_KEY", TEST_API_KEY)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# main mounts StaticFiles(directory="static") at import, resolved against the
# CWD. chdir into app/ ONLY for the import, then restore the CWD so pytest's
# testpaths/collection stay anchored at the repo root (a persistent chdir here
# makes pytest wander into sibling manual scripts).
_orig_cwd = os.getcwd()
os.chdir(APP_DIR)
try:
    import models  # noqa: E402
    import main  # noqa: E402
finally:
    os.chdir(_orig_cwd)

from tests.fakes import FakeLiveKitAPI  # noqa: E402


@pytest.fixture
def dispatch_records():
    """List that records every LiveKit agent dispatch made during a test."""
    return []


@pytest.fixture(autouse=True)
def block_external(monkeypatch, dispatch_records):
    """Replace the LiveKit API with a recording fake so no test performs a
    real agent dispatch / network call. Applied to every test."""
    import livekit.api as livekit_api
    monkeypatch.setattr(livekit_api, "LiveKitAPI", FakeLiveKitAPI(dispatch_records))
    yield


@pytest.fixture
def db_engine():
    """A fresh in-memory SQLite DB with the app's schema, per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def _TestingSessionLocal(db_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture
def db_session(_TestingSessionLocal):
    """A session for seeding/asserting on the same DB the client uses."""
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _make_client(_TestingSessionLocal, headers=None):
    """Build a TestClient bound to the test DB. Not used as a context manager,
    so the app's startup scheduler never runs."""
    def override_get_db():
        db = _TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[models.get_db] = override_get_db
    return TestClient(main.app, headers=headers or {})


@pytest.fixture
def client(_TestingSessionLocal):
    """Authenticated TestClient: sends the API key on every request."""
    test_client = _make_client(_TestingSessionLocal, {"x-api-key": os.environ["API_KEY"]})
    try:
        yield test_client
    finally:
        main.app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(_TestingSessionLocal):
    """TestClient that sends no API key, for testing rejection."""
    test_client = _make_client(_TestingSessionLocal)
    try:
        yield test_client
    finally:
        main.app.dependency_overrides.clear()
