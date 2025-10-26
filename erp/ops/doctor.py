from flask import Blueprint, jsonify, current_app
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic.script import ScriptDirectory
import redis

ops_bp = Blueprint("ops", __name__)

@ops_bp.get("/ops/doctor")
def doctor():
    checks = {}
    ok = True

    # DB
    try:
        url = (current_app.config.get("SQLALCHEMY_DATABASE_URI")
               or current_app.config["DATABASE_URL"])
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["db"] = {"ok": True, "msg": "db ok"}
    except Exception as e:
        ok = False
        checks["db"] = {"ok": False, "msg": str(e)}

    # Redis
    try:
        r = redis.from_url(current_app.config["REDIS_URL"])
        r.ping()
        checks["redis"] = {"ok": True, "msg": "redis ok"}
    except Exception as e:
        ok = False
        checks["redis"] = {"ok": False, "msg": str(e)}

    # Alembic current vs head
    try:
        cfg = Config("alembic.ini")   # lives in /app inside the container
        script = ScriptDirectory.from_config(cfg)
        head = script.get_current_head()
        current = None
        if "db" in checks and checks["db"]["ok"]:
            with engine.connect() as conn:
                current = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        checks["alembic"] = {
            "ok": (current == head),
            "msg": f"current={current} head={head}"
        }
        if current != head:
            ok = False
    except Exception as e:
        ok = False
        checks["alembic"] = {"ok": False, "msg": str(e)}

    return jsonify({"ok": ok, "checks": checks})
