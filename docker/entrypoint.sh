#!/usr/bin/env sh
set -e

# First argument is the role/command (web, migrate, celery, etc.)
cmd="$1"
shift || true

echo "ENTRYPOINT: cmd=${cmd:-<none>} args=$*"

is_prod() {
  [ "${FLASK_ENV:-${ENV:-}}" = "production" ]
}

# In production, do NOT auto-create new Alembic merge revisions at runtime
# unless explicitly enabled.
if is_prod && [ -z "${AUTO_REPAIR_MIGRATIONS:-}" ]; then
  export SKIP_AUTO_MIGRATION_REPAIR=1
fi

# Explicit override: allow auto-repair when you deliberately enable it.
if [ "${AUTO_REPAIR_MIGRATIONS:-0}" = "1" ]; then
  unset SKIP_AUTO_MIGRATION_REPAIR
fi

wait_for_db() {
  # Support both DATABASE_URL and SQLALCHEMY_DATABASE_URI
  DB_URL="${DATABASE_URL:-$SQLALCHEMY_DATABASE_URI}"

  if [ -z "$DB_URL" ]; then
    echo "wait_for_db: no DATABASE_URL or SQLALCHEMY_DATABASE_URI set, skipping DB wait."
    return 0
  fi

  echo "wait_for_db: waiting for DB at $DB_URL"

  python - << 'PY'
import os, time
from sqlalchemy import create_engine

db_url = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
if not db_url:
    print("wait_for_db: no DB URL set in env, exiting early.")
    raise SystemExit(0)

for i in range(30):
    try:
        engine = create_engine(db_url, future=True)
        with engine.connect() as conn:
            # SQLAlchemy 2.x-safe ping
            conn.exec_driver_sql("SELECT 1")
        print("wait_for_db: DB is up.")
        raise SystemExit(0)
    except Exception as exc:
        print(f"wait_for_db: DB not ready yet ({i+1}/30): {exc}")
        time.sleep(1)

print("wait_for_db: ERROR – DB did not become ready in time.")
raise SystemExit(1)
PY
}

repair_migration_heads() {
  if [ -n "$SKIP_AUTO_MIGRATION_REPAIR" ]; then
    echo "repair_migration_heads: skipping (SKIP_AUTO_MIGRATION_REPAIR is set)."
    return 0
  fi

  if [ ! -f tools/repair_migration_heads.py ]; then
    echo "repair_migration_heads: tools/repair_migration_heads.py not found; skipping." >&2
    return 0
  fi

  echo "repair_migration_heads: auto-fixing Alembic heads + upgrading schema…"
  if ! python tools/repair_migration_heads.py; then
    echo "repair_migration_heads: repair script failed." >&2
    return 1
  fi
}

if [ -z "$cmd" ] || [ "$cmd" = "web" ]; then
  wait_for_db
  repair_migration_heads
  echo "Starting Gunicorn web server..."
  exec gunicorn -c gunicorn.conf.py wsgi:app

elif [ "$cmd" = "migrate" ]; then
  wait_for_db
  repair_migration_heads
  echo "Running Alembic migrations (upgrade head)..."
  exec alembic upgrade head

elif [ "$cmd" = "celery" ]; then
  wait_for_db
  repair_migration_heads
  echo "Starting Celery worker with args: $*"
  exec celery "$@"

else
  echo "ENTRYPOINT: executing custom command: $cmd $*"
  exec "$cmd" "$@"
fi
