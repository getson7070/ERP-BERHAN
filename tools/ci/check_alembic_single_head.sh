#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f "alembic.ini" ]]; then
  echo "[skip] alembic.ini not found — skipping single-head check."
  exit 0
fi

if ! command -v alembic >/dev/null 2>&1; then
  echo "alembic not installed; install it to enforce single-head."
  exit 1
fi

out="$(alembic heads 2>&1 || true)"
echo "$out"

# Count lines that mention '(head)'
heads=$(echo "$out" | grep -c "(head)" || true)
if [[ "$heads" -eq 0 ]]; then
  echo "No heads detected — is your migration history initialized?"
  exit 1
fi

if [[ "$heads" -gt 1 ]]; then
  echo "❌ Multiple Alembic heads detected ($heads). Please squash to a single head."
  exit 2
fi

echo "✅ Single Alembic head confirmed."
