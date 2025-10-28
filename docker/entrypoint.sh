#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="/app/wsl-repo:${PYTHONPATH:-}"
export FLASK_APP="${FLASK_APP:-erp.boot:create_app}"
/app/docker/check_migrations.sh || true
exec gunicorn wsgi:app -k eventlet -w 1 -b 0.0.0.0:8000 --log-level=debug