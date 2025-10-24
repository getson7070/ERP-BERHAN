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
