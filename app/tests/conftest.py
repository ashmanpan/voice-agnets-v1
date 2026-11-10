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
os.chdir(APP_DIR)
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

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: E402
import main  # noqa: E402


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


@pytest.fixture
def client(_TestingSessionLocal):
    """A TestClient whose get_db dependency is bound to the test DB.

    Not used as a context manager, so the app's startup scheduler never runs.
    """
    def override_get_db():
        db = _TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[models.get_db] = override_get_db
    test_client = TestClient(main.app)
    try:
        yield test_client
    finally:
        main.app.dependency_overrides.clear()
