from __future__ import annotations
from flask import Blueprint, jsonify
from db import get_db
from .. import redis_client

bp = Blueprint("health", __name__)

def _ping_db() -> bool:
    try:
        get_db().execute("SELECT 1")
        return True
    except Exception:
        return False

def _ping_redis() -> bool:
    try:
        redis_client.set("__ping__", "1")
        redis_client.delete("__ping__")
        return True
    except Exception:
        return False

@bp.get("/health")
def health():
    return jsonify(ok=True), 200

@bp.get("/healthz")
def healthz():
    ok = _ping_db() and _ping_redis()
    return jsonify(ok=ok), (200 if ok else 503)
