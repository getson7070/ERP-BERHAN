from flask import Blueprint, jsonify
import os, socket

bp = Blueprint("health", __name__)

@bp.get("/healthz")
def healthz():
    # simple liveness
    return jsonify(status="ok")

def _can_connect(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False

@bp.get("/readyz")
def readyz():
    db_host   = os.getenv("POSTGRES_HOST", "db")
    db_port   = int(os.getenv("POSTGRES_PORT", "5432"))
    redis_host= os.getenv("REDIS_HOST", "redis")
    redis_port= int(os.getenv("REDIS_PORT", "6379"))

    ok_db    = _can_connect(db_host, db_port)
    ok_redis = _can_connect(redis_host, redis_port)

    status = "ok" if (ok_db and ok_redis) else "degraded"
    code = 200 if status == "ok" else 503
    return jsonify(status=status, db=ok_db, redis=ok_redis), code