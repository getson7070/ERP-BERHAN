#!/bin/sh
# Run Alembic migrations to upgrade database schema.
# Intended to be executed as a separate deployment step before starting the app.
set -euo pipefail

# Prefer explicit overrides so local development can swap in SQLite or
# non-default PostgreSQL URLs without editing alembic.ini.
if [ "${ALEMBIC_URL:-}" != "" ]; then
  alembic -x url="$ALEMBIC_URL" upgrade head
elif [ "${DATABASE_URL:-}" != "" ]; then
  alembic -x url="$DATABASE_URL" upgrade head
else
  alembic upgrade head
fi
