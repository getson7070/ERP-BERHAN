from flask import Blueprint, jsonify, current_app
import os
from sqlalchemy import text, create_engine as sa_create_engine
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

bp = Blueprint("doctor", __name__, url_prefix="/ops")

def _get_engine():
    ext = (current_app.extensions or {}).get("sqlalchemy")
    eng = getattr(ext, "engine", None) if ext else None
    if eng is not None:
        return eng
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    return sa_create_engine(url)

def _check_db():
    try:
        eng = _get_engine()
        if eng is None:
            return False, "no engine and no DATABASE_URL"
        with eng.connect() as c:
            c.execute(text("SELECT 1"))
        return True, "db ok"
    except Exception as e:
        return False, f"db error: {e}"

def _check_alembic_single_head():
    try:
        cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(cfg)
        heads = script.get_heads()
        if len(heads) != 1:
            return False, f"{len(heads)} heads: {heads}"
        eng = _get_engine()
        if eng is None:
            return False, "no engine for alembic current check"
        with eng.connect() as conn:
            ctx = MigrationContext.configure(conn)
            current = ctx.get_current_heads()
        ok = set(current) == set(heads)
        return ok, f"current={list(current)} head={list(heads)}"
    except Exception as e:
        return False, f"alembic error: {e}"

def _check_limiter_backend():
    uri = os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("LIMITER_STORAGE_URI")
    if not uri:
        return False, "FLASK_LIMITER_STORAGE_URI not set"
    if not uri.startswith(("redis://","rediss://","memory://","memcached://")):
        return False, f"unknown limiter scheme: {uri}"
    return True, f"limiter: {uri.split('://',1)[0]}"

def _check_mfa_policy():
    enforced = os.getenv("MFA_ENFORCED", "0").lower() not in ("0","false","off","")
    if not enforced:
        return True, "mfa policy not enforced"
    for r in current_app.url_map.iter_rules():
        if str(r.rule) == "/mfa/setup":
            return True, "mfa enforced & routes present"
    return False, "mfa enforced but /mfa/setup missing"

@bp.get("/doctor")
def doctor():
    checks = {}
    ok = True
    for name, fn in (
        ("db", _check_db),
        ("alembic", _check_alembic_single_head),
        ("limiter", _check_limiter_backend),
        ("mfa_policy", _check_mfa_policy),
    ):
        passed, msg = fn()
        checks[name] = {"ok": passed, "msg": msg}
        ok = ok and passed
    return jsonify({"ok": ok, "checks": checks}), (200 if ok else 503)
from flask import Blueprint, jsonify, current_app
import time, os
bp = Blueprint('doctor', __name__, url_prefix='/ops')
def _check_db():
    try:
        from erp import db
        try:
            db.session.execute('SELECT 1')
            return True, 'ok'
        except Exception as e:
            return False, f'db session error: {e}'
    except Exception:
        try:
            ext = current_app.extensions.get('sqlalchemy')
            if ext and hasattr(ext, 'db'):
                eng = ext.db.engine  # type: ignore
                with eng.connect() as c: c.execute('SELECT 1')
                return True, 'ok'
            return False, 'no sqlalchemy extension'
        except Exception as e:
            return False, f'no db or error: {e}'
def _check_alembic_head():
    try:
        import subprocess, sys
        code = subprocess.call([sys.executable, 'scripts/check_alembic_single_head.py'])
        return (code == 0), f'exit={code}'
    except Exception as e:
        return False, str(e)
def _secret_age_days():
    ts = os.getenv('SECRETS_LAST_ROTATED_TS')
    if not ts: return None
    try:
        return (time.time() - float(ts)) / 86400.0
    except Exception:
        return None
@bp.get('/doctor')
def doctor():
    db_ok, db_msg = _check_db()
    alembic_ok, alembic_msg = _check_alembic_head()
    secrets_age = _secret_age_days()
    return jsonify({
        'ok': db_ok and alembic_ok,
        'checks': {
            'db': {'ok': db_ok, 'msg': db_msg},
            'alembic_single_head': {'ok': alembic_ok, 'msg': alembic_msg},
            'secrets_age_days': secrets_age,
        }
    }), 200 if (db_ok and alembic_ok) else 503
