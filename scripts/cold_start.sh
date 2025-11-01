#!/usr/bin/env bash
set -euo pipefail
alembic upgrade head
python -m erp.scripts.seed_accounts || true
curl -fsS http://localhost:8000/healthz >/dev/null
curl -fsS http://localhost:8000/ops/doctor >/dev/null || true
echo "Cold start OK"
