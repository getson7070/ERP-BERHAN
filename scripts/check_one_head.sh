#!/usr/bin/env bash
set -euo pipefail
HEADS=$(alembic heads | wc -l | tr -d ' ')
if [ "$HEADS" -ne 1 ]; then
  echo "ERROR: Expected single Alembic head, got $HEADS"
  alembic heads
  exit 1
fi
echo "OK: single Alembic head."
