# erp/__init__.py
from __future__ import annotations
import os
from flask import Flask, render_template
from .extensions import (
    db,
    migrate,
    csrf,
    login_manager,
    limiter,
    cache,
    mail,
    socketio,
    cors,
)

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ---- Core config ----
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL") or "sqlite:///app.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Mail
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", "noreply@example.com")

    # CORS
    origins = os.getenv("CORS_ORIGINS")
    if origins:
        cors.init_app(app, resources={r"/*": {"origins": [o.strip() for o in origins.split(",")]}})
    else:
        cors.init_app(app)

    # Cache
    app.config["CACHE_TYPE"] = os.getenv("CACHE_TYPE", "SimpleCache")
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))

    # Limiter
    limiter_storage = os.getenv("FLASK_LIMITER_STORAGE_URI", "memory://")
    limiter.init_app(app, storage_uri=limiter_storage)

    # ---- Init extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, async_mode="eventlet")

    # ---- Flask-Login ----
    from .models import User  # local import to avoid circular
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # ---- Blueprints ----
    from .routes.main import main_bp
    from .routes.auth import bp as auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # ---- Error pages ----
    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    return app
