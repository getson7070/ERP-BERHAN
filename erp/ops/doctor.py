from flask import Blueprint, jsonify, current_app
import os, subprocess, sys

bp = Blueprint("doctor", __name__, url_prefix="/ops")

def _check_db():
    try:
        ext = current_app.extensions.get("sqlalchemy")
        if not ext:
            return False, "sqlalchemy extension not found"
        db = ext.db  # type: ignore[attr-defined]
        with db.engine.connect() as c:
            c.execute("SELECT 1")
        return True, "db ok"
    except Exception as e:
        return False, f"db error: {e}"

def _check_alembic_single_head():
    try:
        code = subprocess.call([sys.executable, "scripts/check_alembic_single_head.py"])
        return (code == 0), f"check_alembic_single_head exit={code}"
    except Exception as e:
        return False, f"alembic check error: {e}"

def _check_limiter_backend():
    uri = os.getenv("FLASK_LIMITER_STORAGE_URI") or os.getenv("LIMITER_STORAGE_URI")
    if not uri:
        return False, "FLASK_LIMITER_STORAGE_URI not set"
    ok_schemes = ("redis://", "rediss://", "memory://", "memcached://")
    if not any(uri.startswith(s) for s in ok_schemes):
        return False, f"unknown limiter scheme: {uri}"
    return True, f"limiter: {uri.split('://',1)[0]}"
    
def _check_mfa_policy():
    enforced = os.getenv("MFA_ENFORCED", "0") not in ("0", "false", "False", "off", "")
    if not enforced:
        return True, "mfa policy not enforced"
    for r in current_app.url_map.iter_rules():
        if str(r.rule) == "/mfa/setup":
            return True, "mfa enforced & routes present"
    return False, "mfa enforced but /mfa/setup route missing"

@bp.get("/doctor")
def doctor():
    checks = {}
    ok = True
    for name, fn in (
        ("db", _check_db),
        ("alembic_single_head", _check_alembic_single_head),
        ("limiter_backend", _check_limiter_backend),
        ("mfa_policy", _check_mfa_policy),
    ):
        try:
            passed, msg = fn()
        except Exception as e:
            passed, msg = False, f"exception: {e}"
        checks[name] = {"ok": passed, "msg": msg}
        ok = ok and passed
    status = 200 if ok else 503
    return jsonify({"ok": ok, "checks": checks}), status