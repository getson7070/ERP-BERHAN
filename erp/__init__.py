# erp/__init__.py
from __future__ import annotations

import os
from flask import Flask, render_template
from .extensions import (
    db,
    migrate,
    login_manager,
    cors,
    cache,
    mail,
    limiter,
)
# IMPORTANT: don't import routes or security at module import time.

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # --- Config
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Rate limit storage (Flask-Limiter v3.x): use app.config key
    app.config.setdefault("RATELIMIT_STORAGE_URI", os.getenv("RATELIMIT_STORAGE_URI") or os.getenv("FLASK_LIMITER_STORAGE_URI") or "memory://")

    # Cache
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")))

    # Mail
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

    # --- Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})
    cache.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)  # storage URI comes from app.config

    # --- Error pages
    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # --- Register blueprints (import inside function)
    from .routes.main import main_bp
    from .routes.auth import bp as auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    return app
