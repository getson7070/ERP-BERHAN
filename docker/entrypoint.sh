#!/usr/bin/env bash
set -euo pipefail

echo "[boot] DATABASE_URL=${DATABASE_URL:-<missing>}"
export PORT="${PORT:-18000}"

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local tries="${3:-60}"

  python - <<PY
import socket, sys, time
host = "${host}"
port = int("${port}")
tries = int("${tries}")
for i in range(tries):
    try:
        with socket.create_connection((host, port), timeout=1):
            print(f"[boot] TCP ready: {host}:{port}")
            sys.exit(0)
    except Exception:
        time.sleep(1)
print(f"[boot] TCP not ready after {tries}s: {host}:{port}")
sys.exit(1)
PY
}

# Wait for DB and Redis sockets
wait_for_tcp "db" "5432" "90"
wait_for_tcp "redis" "6379" "90"

# Run migrations
if [ "${ALEMBIC_AUTO_UPGRADE:-true}" = "true" ]; then
  echo "[boot] Running alembic upgrade head..."
  alembic upgrade head
fi

# Run baseline seed
if [ "${INIT_DB_ON_BOOT:-true}" = "true" ]; then
  echo "[boot] Running init_db.py..."
  python init_db.py
fi

echo "[boot] Starting app on port ${PORT}..."
# Ensure gunicorn binds to PORT even if CMD is overridden elsewhere
exec gunicorn -b "0.0.0.0:${PORT}" -w "${WEB_CONCURRENCY:-2}" wsgi:app
