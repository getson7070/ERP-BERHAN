#!/bin/sh
set -euo pipefail

ROLE="${1:-web}"
: "${FLASK_APP:=erp:create_app}"

echo "[entrypoint] Role: $ROLE  FLASK_APP=$FLASK_APP"

if [ "$ROLE" = "web" ]; then
  flask db upgrade || echo "[warn] migrations failed (continuing)"
  exec gunicorn -c gunicorn.conf.py wsgi:app
elif [ "$ROLE" = "worker" ]; then
  flask db upgrade || true
  exec celery -A erp.celery_app worker -l info
elif [ "$ROLE" = "beat" ]; then
  exec celery -A erp.celery_app beat -l info
else
  echo "Unknown role: $ROLE"; exit 2
fi
