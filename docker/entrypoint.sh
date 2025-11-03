#!/usr/bin/env bash
set -euo pipefail

# ---- Options / defaults ----
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-erp}"
DB_NAME="${DB_NAME:-erp}"
# DATABASE_URL may be set by your env; else our env.py already falls back
export PYTHONPATH=/app

# ---- Wait for Postgres to accept connections ----
if command -v pg_isready >/dev/null 2>&1; then
  until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
    echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT}..." ; sleep 1
  done
else
  # Fallback if pg_isready is not present
  until (echo >/dev/tcp/${DB_HOST}/${DB_PORT}) >/dev/null 2>&1; do
    echo "Waiting for Postgres (tcp) at ${DB_HOST}:${DB_PORT}..." ; sleep 1
  done
fi

# ---- Run migrations idempotently ----
cd /app
alembic upgrade head

# ---- Hand off to the container command ----
exec "$@"

