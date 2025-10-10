# erp/__init__.py
from __future__ import annotations

import os
from flask import Flask, render_template
from flask_cors import CORS
from .extensions import (
    db,
    migrate,
    login_manager,
    cache,
    mail,
    limiter,
    socketio,
)
# IMPORTANT: this repo has security_shim, not security.device
from .security_shim import read_device_id, compute_activation_for_device  # noqa: F401


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # --- Config (Render env already provides these) ---
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
    app.config["WTF_CSRF_SECRET_KEY"] = os.environ.get("WTF_CSRF_SECRET_KEY", "dev-csrf")
    app.config["CACHE_TYPE"] = os.environ.get("CACHE_TYPE", "SimpleCache")
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "300"))

    cors_origins = os.environ.get("CORS_ORIGINS", "*")
    CORS(app, resources={r"/*": {"origins": cors_origins}})

    # --- Init extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    mail.init_app(app)

    # Limiter 3.x: no storage_uri kw here; honor DEFAULT_RATE_LIMITS env
    default_limits = [x.strip() for x in os.environ.get("DEFAULT_RATE_LIMITS", "").split(";") if x.strip()]
    limiter.init_app(app, default_limits=default_limits or None)

    # Socket.IO (eventlet workers on Render)
    socketio.init_app(app, cors_allowed_origins=cors_origins)

    # --- Login manager user_loader ---
    from .models import User  # local import to avoid circulars

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.login"

    # --- Blueprints ---
    from .routes.main import main_bp
    from .routes.auth import bp as auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # --- Error handlers (keep them template-safe even if login context exists) ---
    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_):
        return render_template("errors/500.html"), 500

    return app
