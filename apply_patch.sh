#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "[1/6] Copying ops files (gunicorn, wsgi_eventlet, render snippet)..."
cp -f "$ROOT/patches/ops/gunicorn.conf.py" "$ROOT/gunicorn.conf.py"
cp -f "$ROOT/patches/ops/wsgi_eventlet.py" "$ROOT/wsgi_eventlet.py"
mkdir -p "$ROOT/ops"
cp -f "$ROOT/patches/ops/render.patch.yaml" "$ROOT/ops/render.patch.yaml"

echo "[2/6] Hardening Alembic config..."
cp -f "$ROOT/patches/alembic.ini" "$ROOT/alembic.ini"
cp -f "$ROOT/patches/migrations/env.py" "$ROOT/migrations/env.py"

echo "[3/6] Adding security & blueprints/models..."
mkdir -p "$ROOT/erp/security" "$ROOT/erp/blueprints" "$ROOT/erp/models" "$ROOT/bots" "$ROOT/scripts"
cp -f "$ROOT/patches/erp/security/input_sanitizer.py" "$ROOT/erp/security/input_sanitizer.py"
cp -f "$ROOT/patches/erp/blueprints/"* "$ROOT/erp/blueprints/"
cp -f "$ROOT/patches/erp/models/"* "$ROOT/erp/models/"
cp -f "$ROOT/patches/bots/slack_app.py" "$ROOT/bots/slack_app.py"

echo "[4/6] Adding helper scripts & tests..."
cp -f "$ROOT/patches/scripts/"* "$ROOT/scripts/"
mkdir -p "$ROOT/tests"
cp -f "$ROOT/patches/tests/"* "$ROOT/tests/"

echo "[5/6] Append new requirements (eventlet, slack, bleach) if not present..."
APPEND="$ROOT/patches/requirements.append.txt"
REQ="$ROOT/requirements.txt"
touch "$REQ"
while IFS= read -r line; do
  if [ -n "$line" ] && ! grep -qiE "^${line}$" "$REQ"; then
    echo "$line" >> "$REQ"
  fi
done < "$APPEND"

echo "[6/6] Done. Next:"
echo " - pip install -r requirements.txt"
echo " - bash scripts/create_migration_and_upgrade.sh"
echo " - set env: GUNICORN_WORKER_CLASS=eventlet, PROMETHEUS_MULTIPROC_DIR=/tmp/prom"
echo " - point your process to 'wsgi_eventlet:app'"
