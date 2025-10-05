# erp/app.py
from __future__ import annotations
import logging
from flask import Flask
from .extensions import db, migrate, cache, limiter, login_manager, cors
from .routes.auth import auth_bp
from .web import web_bp
from .models import User

log = logging.getLogger("erp.app")

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # Base config (Render env provides URLs/keys)
    app.config.from_mapping(
        SECRET_KEY = app.config.get("SECRET_KEY", "change-me"),
        SQLALCHEMY_DATABASE_URI = app.config.get("SQLALCHEMY_DATABASE_URI"),
        SQLALCHEMY_TRACK_MODIFICATIONS = False,
        CACHE_TYPE = app.config.get("CACHE_TYPE", "SimpleCache"),
        CACHE_DEFAULT_TIMEOUT = int(app.config.get("CACHE_DEFAULT_TIMEOUT", 300)),
    )

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id: str):
        # Required by Flask-Login; returning None means "not logged in"
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # Blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)

    # Optional: Prometheus/metrics, Socket.IO, etc. (left out for clarity)

    # Log what blueprints we actually have
    log.info("Blueprints: %s", list(app.blueprints.keys()))
    return app
