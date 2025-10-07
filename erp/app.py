import os
from flask import Flask, redirect, url_for, render_template

# all extensions are created in extensions.py
from .extensions import (
    db, migrate, cache, limiter, login_manager, mail, socketio, init_extensions
)


def _make_app_config() -> dict:
    """
    Build a minimal config from environment with safe defaults.
    Flask-Limiter 3.x reads defaults from RATELIMIT_* keys.
    """
    cfg = {}

    # DB config (Render sets DATABASE_URL; Flask prefers SQLALCHEMY_DATABASE_URI)
    db_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if db_url:
        cfg["SQLALCHEMY_DATABASE_URI"] = db_url

    # Caching
    cfg["CACHE_TYPE"] = os.getenv("CACHE_TYPE", "SimpleCache")
    if os.getenv("CACHE_DEFAULT_TIMEOUT"):
        cfg["CACHE_DEFAULT_TIMEOUT"] = int(os.getenv("CACHE_DEFAULT_TIMEOUT"))

    # Flask secret
    if os.getenv("FLASK_SECRET_KEY"):
        cfg["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

    # --- Flask-Limiter 3.8+ ---
    # Storage backend
    storage_uri = (
        os.getenv("FLASK_LIMITER_STORAGE_URI")
        or os.getenv("RATELIMIT_STORAGE_URI")
        or "memory://"
    )
    cfg["RATELIMIT_STORAGE_URI"] = storage_uri

    # Default limits: must be a single string like "300 per minute; 30 per second"
    limits_str = (
        os.getenv("DEFAULT_RATE_LIMITS")
        or os.getenv("RATELIMIT_DEFAULT")
        or os.getenv("RATELIMIT_DEFAULTS")
        or "300 per minute; 30 per second"
    )
    # normalize a few common mistakes
    limits_str = limits_str.strip().strip("[]").replace(",", ";")
    cfg["RATELIMIT_DEFAULT"] = limits_str

    # CORS (optional)
    if os.getenv("CORS_ORIGINS"):
        cfg["CORS_ORIGINS"] = os.getenv("CORS_ORIGINS")

    # entry template (only used by the fallback index below)
    cfg["ENTRY_TEMPLATE"] = os.getenv("ENTRY_TEMPLATE", "choose_login.html")

    return cfg


def create_app() -> Flask:
    base_dir = os.path.dirname(__file__)
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )

    # Load config, then init extensions
    app.config.update(_make_app_config())
    init_extensions(app)

    # ----- Blueprints -----
    # Auth blueprint (we provide a compatible auth.py below exporting auth_bp)
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Web/UI blueprint is optional; if present register it, otherwise we fallback
    try:
        from .routes.web import web_bp  # must define Blueprint("web", __name__)
        app.register_blueprint(web_bp)
    except Exception:
        # No web blueprint? It's fine; we'll provide fallback routes below.
        pass

    # ----- Fallback routes if web blueprint is missing -----
    @app.get("/")
    def index():
        # Prefer existing web.login_page if present (keeps old URLs working)
        if "web.login_page" in app.view_functions:
            return redirect(url_for("web.login_page"))
        # Otherwise render the configured entry template directly
        return render_template(app.config.get("ENTRY_TEMPLATE", "choose_login.html"))

    @app.get("/health")
    def health():
        return "ok"

    return app
