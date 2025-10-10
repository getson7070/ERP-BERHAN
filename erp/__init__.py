# erp/__init__.py
"""
App factory for Berhan ERP.

Key points:
- eventlet.monkey_patch() happens FIRST (required by eventlet workers).
- Safe defaults for SECRET_KEY / CSRF and DB URI so Alembic can run.
- Blueprints: main (public pages) and auth (auth flows).
- Flask-Login is initialized and minimal loaders are registered via erp.auth_loaders.
- Error handlers render branded templates without crashing.
"""

# -------------------------------------------------------------------
# 1) Eventlet must patch BEFORE importing anything that uses sockets.
# -------------------------------------------------------------------
try:
    import eventlet

    eventlet.monkey_patch()  # patches stdlib for cooperative I/O
except Exception:
    # If eventlet isn't installed (e.g., local non-socketio runs), carry on.
    pass

import os
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

# Extensions (created in .extensions, but NOT init_app'ed yet)
from .extensions import (
    db,
    migrate,
    csrf,
    cors,
    limiter,
    login_manager,
    socketio,
)


def _bool(env_value: str, default: bool = False) -> bool:
    if env_value is None:
        return default
    return env_value.strip().lower() in {"1", "true", "yes", "on"}


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )

    # ---------------------------------------------------------------
    # 2) Core configuration with safe fallbacks (so Alembic can run)
    # ---------------------------------------------------------------
    app.config["ENV"] = os.getenv("FLASK_ENV", "production")
    app.config["DEBUG"] = _bool(os.getenv("FLASK_DEBUG"), False)

    # Secrets / CSRF
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me-berhan-erp")
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_TIME_LIMIT"] = None
    app.config["WTF_CSRF_SECRET_KEY"] = os.getenv(
        "WTF_CSRF_SECRET_KEY", app.config["SECRET_KEY"]
    )

    # Database: prefer DATABASE_URL (Render/Heroku style), else local sqlite
    db_uri = os.getenv("DATABASE_URL")
    if db_uri and db_uri.startswith("postgres://"):
        # SQLAlchemy 2.x requires postgresql://
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri or "sqlite:////tmp/berhan_erp.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # CORS (allow your frontend origin if present)
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    app.config["CORS_ORIGINS"] = [o.strip() for o in cors_origins.split(",") if o.strip()]

    # Rate limit storage: default in-memory (ok for now since Redis is optional)
    # If you later enable Redis, set: LIMITER_STORAGE_URI=redis://...
    app.config["RATELIMIT_DEFAULT"] = "100 per minute"
    app.config["RATELIMIT_STORAGE_URI"] = os.getenv("LIMITER_STORAGE_URI", "memory://")

    # Socket.IO
    app.config["SOCKETIO_CORS_ALLOWED_ORIGINS"] = app.config["CORS_ORIGINS"]

    # Make sure we respect reverse proxy headers on Render
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # ---------------------------------------------------------------
    # 3) Initialize extensions
    # ---------------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})
    limiter.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Register minimal Flask-Login loaders (prevents 500 on public pages)
    # This import has side-effects that register @user_loader, etc.
    from . import auth_loaders  # noqa: F401

    # Socket.IO (only used if you wire up websocket features)
    socketio.init_app(
        app,
        cors_allowed_origins=app.config["SOCKETIO_CORS_ALLOWED_ORIGINS"],
        async_mode="eventlet",  # matches your Gunicorn worker
        logger=False,
        engineio_logger=False,
    )

    # ---------------------------------------------------------------
    # 4) Register blueprints
    # ---------------------------------------------------------------
    from .routes.main import main_bp
    from .routes.auth import auth_bp

    # Public/main site (/, /choose_login, /help, /privacy, /feedback, /health)
    app.register_blueprint(main_bp)

    # Auth endpoints live under /auth/*
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # ---------------------------------------------------------------
    # 5) Error handlers (render branded pages without crashing)
    # ---------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(_e):
        # Keep this template simple: no dynamic links that could build wrong endpoints
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def too_many_requests(_e):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(_e):
        # Avoid referencing endpoints directly in base layout for error pages
        return render_template("errors/500.html"), 500

    # ---------------------------------------------------------------
    # 6) Jinja globals / brand helpers (logo path, year)
    # ---------------------------------------------------------------
    @app.context_processor
    def inject_brand():
        return {
            "brand_name": "Berhan ERP",
            # Use the exact path you placed in repo:
            "brand_logo_path": "/static/pictures/BERHAN-PHARMA-LOGO.jpg",
            "current_year": 2025,
        }

    return app
