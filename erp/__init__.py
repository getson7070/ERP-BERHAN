# erp/__init__.py
from __future__ import annotations

import os
from pathlib import Path
from flask import Flask
from flask_socketio import SocketIO

from .extensions import db  # SQLAlchemy instance
from .app import init_security, register_blueprints  # your helpers in erp/app.py
from config import Config

# Exported for wsgi/gunicorn
socketio: SocketIO | None = None


def _ensure_instance_dir(app: Flask) -> None:
    """Make sure instance dir exists (needed for SQLite & file-based config)."""
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)


def _apply_safe_defaults(app: Flask) -> None:
    """
    Make the app runnable out-of-the-box when critical env vars are missing.
    - Use SQLite for quick demos (no Postgres required).
    - Allow FakeRedis to avoid a real Redis during dev/preview.
    """
    # Database
    if not os.environ.get("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(app.instance_path) / 'erp.db'}"
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

    # Redis / message queue
    if os.environ.get("USE_FAKE_REDIS") is None:
        # default to FakeRedis in non-production
        if app.config.get("APP_ENV", "development") != "production":
            os.environ["USE_FAKE_REDIS"] = "1"

    # Minimal required secrets for dev/preview
    app.config.setdefault("SECRET_KEY", os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY") or "dev-secret")
    app.config.setdefault("JWT_SECRET_KEY", os.environ.get("JWT_SECRET_KEY") or "dev-jwt")
    app.config.setdefault("SECURITY_PASSWORD_SALT", os.environ.get("SECURITY_PASSWORD_SALT") or "dev-salt")


def create_app(config_class: type[Config] = Config) -> Flask:
    """
    Application factory. Initializes:
      - Config
      - Instance dir
      - SQLAlchemy
      - Security + JWT (via erp/app.py)
      - Blueprints (auto-discovery)
      - Socket.IO (eventlet)
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    _ensure_instance_dir(app)
    _apply_safe_defaults(app)

    # DB
    db.init_app(app)

    # Security & JWT (your helper wires flask-security-too + flask_jwt_extended)
    init_security(app)

    # Blueprints (your helper auto-discovers and registers)
    register_blueprints(app)

    # Create tables automatically only when using SQLite (quick preview/demo)
    # Avoid doing this for Postgres in production.
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("sqlite:"):
        with app.app_context():
            db.create_all()

    # Socket.IO
    global socketio
    if socketio is None:
        # In production on Render you run gunicorn with eventlet worker class.
        # message_queue=None uses in-process (works with 1 dyno). Set REDIS_URL to scale.
        socketio = SocketIO(
            async_mode="eventlet",
            cors_allowed_origins="*",
            message_queue=os.environ.get("SOCKETIO_MESSAGE_QUEUE"),  # e.g. redis://...
        )
        socketio.init_app(app)

    return app
