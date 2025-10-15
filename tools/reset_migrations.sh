#!/usr/bin/env bash
set -euo pipefail
echo "[reset] THIS WILL REWRITE migrations/versions/*.py — make sure you are on a dev DB."
alembic downgrade base || true
rm -rf migrations/versions/*
alembic revision --autogenerate -m "init schema"
alembic upgrade head
echo "[reset] Done. Commit the new migrations/versions/* files."
