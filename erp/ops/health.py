
from flask import Blueprint, jsonify
try:
    from flask import current_app
    from flask_sqlalchemy import SQLAlchemy
except Exception:
    SQLAlchemy = None  # optional

bp = Blueprint("ops", __name__)

@bp.get("/healthz")
def healthz():
    return jsonify(status="ok"), 200

@bp.get("/readyz")
def readyz():
    try:
        # Optional DB ping if SQLAlchemy bound
        if SQLAlchemy is not None and hasattr(current_app, "extensions") and "sqlalchemy" in current_app.extensions:
            db = current_app.extensions["sqlalchemy"]["db"]
            with db.engine.connect() as conn:
                conn.execute("SELECT 1")
    except Exception as e:
        return jsonify(status="degraded", detail=str(e)), 503
    return jsonify(status="ready"), 200
