#!/bin/sh
# Apply DB migrations before starting the app, so the schema always matches
# the models (replaces the stale database/schema.sql init).
set -e
echo "Running database migrations (alembic upgrade head)..."
PYTHONPATH=/app alembic upgrade head
exec "$@"
