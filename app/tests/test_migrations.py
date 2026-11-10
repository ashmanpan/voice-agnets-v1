"""Verify Alembic migrations build a schema matching the SQLAlchemy models.
Guards against migrations drifting from models.py."""
import os

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

import models

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_migrations_create_all_model_tables(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    monkeypatch.setenv("DATABASE_URL", url)

    cfg = Config(os.path.join(REPO_ROOT, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(REPO_ROOT, "migrations"))
    command.upgrade(cfg, "head")

    tables = set(inspect(create_engine(url)).get_table_names())
    expected = set(models.Base.metadata.tables.keys())
    assert expected <= tables, f"missing tables after migrate: {expected - tables}"
