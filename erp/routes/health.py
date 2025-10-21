﻿from flask import Blueprint, jsonify
import os, sqlite3
from erp import redis_client

bp = Blueprint("health", __name__)

def _ping_db() -> bool:
    path = os.environ.get("DATABASE_PATH")
    try:
        with sqlite3.connect(path or ":memory:") as c:
            c.execute("SELECT 1")
        return True
    except Exception:
        return False

def _ping_redis() -> bool:
    try:
        redis_client.delete("__health__")
        return True
    except Exception:
        return False

@bp.get("/health")
def health():
    return jsonify({"ok": True, "status": "ok"})

@bp.get("/healthz")
def healthz():
    ok_db = _ping_db()
    ok_redis = _ping_redis()
    ok = ok_db and ok_redis
    return jsonify({"ok": ok, "status": "ok" if ok else "degraded", "db": ok_db, "redis": ok_redis}), (200 if ok else 503)

@bp.get("/readyz")
def readyz():
    ready = _ping_db() and _ping_redis()
    return jsonify({"status": "ok" if ready else "not_ready", "ready": ready}), (200 if ready else 503)
