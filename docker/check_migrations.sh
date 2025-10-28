#!/usr/bin/env sh
set -e
if command -v alembic >/dev/null 2>&1; then
  alembic upgrade head || true
elif command -v flask >/dev/null 2>&1; then
  flask db upgrade || true
fi