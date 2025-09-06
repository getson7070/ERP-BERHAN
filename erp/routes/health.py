from __future__ import annotations
from flask import Blueprint, jsonify
import os
from erp import talisman

bp = Blueprint("health", __name__)


def _ping_db() -> bool:
    try:
        from db import get_engine
        from sqlalchemy import text

        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _ping_redis() -> bool:
    url = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL")
    if not url:
        # Redis is optional; treat absence of a configured URL as healthy
        return True
    try:
        import redis

        r = redis.Redis.from_url(url)
        r.ping()
        return True
    except Exception:
        return False


@bp.get("/health")
@talisman(force_https=False)
def health():
    return jsonify(ok=True), 200


@bp.get("/healthz")
@talisman(force_https=False)
def healthz():
    db_ok = _ping_db()
    redis_ok = _ping_redis()
    ok = db_ok and redis_ok
    return jsonify(ok=ok, db=db_ok, redis=redis_ok), (200 if ok else 503)
