#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL must be set}"
echo "[migrate] Running Alembic migrations..."
alembic upgrade head
echo "[migrate] Done."
