from __future__ import annotations

import os
import logging
from pathlib import Path

try:
    import eventlet
    eventlet.monkey_patch()
except Exception:
    pass

from flask import Flask, jsonify
from .extensions import db, migrate, cache, limiter, login_manager, cors
from .models import User

log = logging.getLogger(__name__)

def _split_limits(value: str | None) -> list[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(";") if p.strip()]

def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent.parent / "templates"))

    app.config.from_mapping(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI") or
                                 os.getenv("DATABASE_URL") or "sqlite:///erp.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CACHE_TYPE=os.getenv("CACHE_TYPE", "SimpleCache"),
        CACHE_DEFAULT_TIMEOUT=int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),
        RATELIMIT_STORAGE_URI=os.getenv("RATELIMIT_STORAGE_URI", os.getenv("FLASK_LIMITER_STORAGE_URI", "memory://")),
        DEFAULT_RATE_LIMITS=os.getenv("DEFAULT_RATE_LIMITS", ""),
        CORS_ORIGINS=os.getenv("CORS_ORIGINS", "*"),
        APP_ENV=os.getenv("APP_ENV", "development"),
    )

    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    limits = _split_limits(app.config.get("DEFAULT_RATE_LIMITS"))
    try:
        limiter.init_app(app, default_limits=limits, storage_uri=app.config["RATELIMIT_STORAGE_URI"])
    except TypeError:
        limiter.init_app(app, default_limits=limits)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    @login_manager.unauthorized_handler
    def _unauth():
        return jsonify({"error": "unauthorized"}), 401

    try:
        cors.init_app(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})
    except Exception:
        cors.init_app(app)

    from .web import web_bp
    from .routes.auth import auth_bp
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            log.exception("DB init failed: %s", e)

    return app
