"""Health check endpoints for container orchestration probes.

The application exposes two aliases, ``/health`` and ``/healthz``, both of
which perform lightweight dependency checks to keep Kubernetes and Docker
probes happy.  Only a trivial ``SELECT 1`` is executed against the database to
avoid expensive operations and, when configured, Redis is pinged to confirm the
cache layer is reachable.
"""

from flask import Blueprint, jsonify

from db import get_db, redis_client

bp = Blueprint("health", __name__)


@bp.route("/health")
@bp.route("/healthz")
def health() -> tuple[dict, int]:
    """Return basic service status along with dependency checks."""

    db_ok = True
    redis_ok = True
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
    except Exception:  # pragma: no cover - best effort
        db_ok = False
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:  # pragma: no cover - best effort
            pass

    try:  # pragma: no cover - best effort
        redis_client.ping()
    except Exception:
        redis_ok = False

    status = "ok" if db_ok and redis_ok else "degraded"
    payload = {"status": status, "db": db_ok, "redis": redis_ok}
    return jsonify(payload), 200
