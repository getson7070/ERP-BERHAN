from __future__ import annotations
from flask import Blueprint, jsonify, current_app, request
from sqlalchemy import text
from db import get_engine, redis_client

bp = Blueprint("health", __name__)

def _ping_db() -> bool:
    try:
        eng = get_engine()
        with eng.connect() as c:
            c.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

@bp.get("/health")
def health():
    return jsonify({"status":"ok"})

@bp.get("/healthz")
def healthz():
    ok = _ping_db()
    if not ok:
        return jsonify({"status":"fail"}), 503
    return jsonify({"status":"ok"})

@bp.get("/readyz")
def readyz():
    ready = _ping_db()
    return jsonify({"ready": bool(ready), "status": "ready" if ready else "not_ready"}), 200 if ready else 503
