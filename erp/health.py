from flask import Blueprint, jsonify
import os
from sqlalchemy import text
from .extensions import db

bp = Blueprint("health", __name__)


@bp.get("/healthz")
def healthz():
    details = {}
    ok_db = True
    try:
        with db.engine.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception as e:
        ok_db = False
        details["db_error"] = str(e)

    ok_redis = True
    ru = os.getenv("REDIS_URL")
    if ru:
        try:
            import redis

            redis.Redis.from_url(ru).ping()
        except Exception as e:
            ok_redis = False
            details["redis_error"] = str(e)

    status = "ok" if ok_db and ok_redis else "degraded"
    return jsonify(status=status, **details), (200 if status == "ok" else 503)
