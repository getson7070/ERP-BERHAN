# erp/app.py
"""
Flask application factory for ERP-BERHAN.

This replacement fixes the runtime error:
  NameError: name 'Flask' is not defined

It provides a proper create_app() that:
- Imports and initializes Flask and extensions
- Loads config from environment (DATABASE_URL / SQLALCHEMY_DATABASE_URI, SECRET_KEY, etc.)
- Enables CORS
- Registers available blueprints (e.g., /api/integrations)
- Exposes simple / and /healthz endpoints
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS

# Local extensions (SQLAlchemy, optional SocketIO) and their initializer
from .extensions import init_extensions

# Blueprints (register only if present)
try:
    from .api.integrations import bp as integrations_bp
except Exception:
    integrations_bp = None


def create_app() -> Flask:
    """Application factory used by wsgi.py (gunicorn loads `wsgi:app`)."""
    app = Flask(__name__, instance_relative_config=True)

    # ---- Base config (env-driven, with sensible fallbacks) -----------------
    # Prefer DATABASE_URL (Render) then SQLALCHEMY_DATABASE_URI, else local sqlite.
    db_uri = (
        os.getenv("DATABASE_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URI")
        or "sqlite:///dev.db"
    )

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "change-me"),
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
        # JWT libs (if used elsewhere) can reuse SECRET_KEY by default
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "change-me")),
    )

    # ---- CORS (open by default; tighten in production if you know the origins) ---
    CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

    # ---- Initialize extensions (db, socketio-if-installed, etc.) ---------------
    init_extensions(app)

    # ---- Blueprints -------------------------------------------------------------
    if integrations_bp is not None:
        app.register_blueprint(integrations_bp, url_prefix="/api/integrations")

    # ---- Basic health endpoints -------------------------------------------------
    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.get("/")
    def root():
        return jsonify(app="ERP-BERHAN", status="running")

    return app
