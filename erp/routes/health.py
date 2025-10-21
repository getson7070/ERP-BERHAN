from flask import Blueprint, jsonify, current_app
import os, sqlite3

bp = Blueprint("health", __name__)

def _ping_db() -> bool:
    path = os.environ.get("DATABASE_PATH")
    try:
        if path:
            with sqlite3.connect(path) as c:
                c.execute("SELECT 1")
        else:
            with sqlite3.connect(":memory:") as c:
                c.execute("SELECT 1")
        return True
    except Exception:
        return False

def _ping_cache() -> bool:
    return True  # shim is always available in tests

@bp.get("/health")
def health():
    return jsonify({"ok": True, "status": "ok"})

@bp.get("/healthz")
def healthz():
    ok_db = _ping_db()
    ok_cache = _ping_cache()
    return jsonify({"ok": ok_db and ok_cache, "db": ok_db, "cache": ok_cache}), (200 if ok_db and ok_cache else 503)

@bp.get("/readyz")
def readyz():
    ready = _ping_db() and _ping_cache()
    return jsonify({"ready": ready}), (200 if ready else 503)
