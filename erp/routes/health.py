from __future__ import annotations
from flask import Blueprint, jsonify
import os
import redis
from db import get_db

bp = Blueprint("health", __name__)

def _ping_db() -> bool:
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return True
    except Exception:
        return False

def _ping_redis() -> bool:
    try:
        url = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL") or "redis://localhost:6379/0"
        r = redis.Redis.from_url(url)
        r.ping()
        return True
    except Exception:
        return False

@bp.get("/health")
def health():
    return jsonify(ok=True), 200

@bp.get("/healthz")
def healthz():
    db_ok = _ping_db()
    redis_ok = _ping_redis()
    ok = db_ok and redis_ok
    return jsonify(ok=ok, db=db_ok, redis=redis_ok), (200 if ok else 503)
