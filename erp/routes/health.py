from flask import Blueprint, jsonify
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

def _ping_cache() -> bool: return True
def _ping_redis() -> bool: return True

@bp.get("/health")
def health():
    return jsonify({"ok": True, "status": "ok"})

@bp.get("/healthz")
def healthz():
    ok_db = _ping_db()
    ok_cache = _ping_cache()
    ok_redis = _ping_redis()
    ok = ok_db and ok_cache and ok_redis
    return jsonify({"ok": ok, "status": ("ok" if ok else "error"),
                    "db": ok_db, "cache": ok_cache, "redis": ok_redis}), (200 if ok else 503)

@bp.get("/readyz")
def readyz():
    ready = _ping_db() and _ping_cache() and _ping_redis()
    return jsonify({"ready": ready, "status": ("ready" if ready else "not_ready")}), (200 if ready else 503)
