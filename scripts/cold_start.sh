#!/usr/bin/env bash
set -euo pipefail

echo "Running Alembic migrations..."
alembic upgrade head

echo "Seeding phase-1 users & defaults (idempotent)..."
python -m erp.bootstrap_phase1 --seed --admin-email admin@local.test --admin-password 'Dev!23456' --force

echo "Doctor:"
curl -fsS http://localhost:8000/ops/doctor || true
