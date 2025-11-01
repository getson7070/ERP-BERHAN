#!/usr/bin/env bash
set -euo pipefail
# Count heads without using $(...) in PowerShell-exec
hcount="$(alembic heads | wc -l | tr -d "[:space:]")"
if [ "$hcount" -ne 1 ]; then
  echo "[FATAL] Multiple Alembic heads detected:" >&2
  alembic heads -v >&2
  exit 1
fi
alembic upgrade head
