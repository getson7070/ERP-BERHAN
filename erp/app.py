# erp/app.py
from __future__ import annotations
import os
from importlib import import_module
from pathlib import Path
from typing import Iterable

from flask import Flask, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import (
    db, cache, compress, csrf, babel, jwt, limiter, socketio, oauth
)

DEFAULT_LIMITS = ["2000 per hour", "20000 per day"]  # tune for prod

def _load_config(app: Flask) -> None:
    app.config.setdefault("SECRET_KEY", os.getenv("FLASK_SECRET_KEY", "change-me"))
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URL", "sqlite:///instance/erp_dev.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Cache / Limiter backends (Redis recommended in prod)
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 300)

    limiter_backend = os.getenv("RATELIMIT_STORAGE_URI")  # e.g., "redis://:pass@host:6379/0"
    if limiter_backend:
        app.config["RATELIMIT_STORAGE_URI"] = limiter_backend

    # JWT
    app.config.setdefault("JWT_SECRET_KEY", os.getenv("JWT_SECRET", app.config["SECRET_KEY"]))

    # Babel
    app.config.setdefault("BABEL_DEFAULT_LOCALE", os.getenv("BABEL_DEFAULT_LOCALE", "en"))

    # SocketIO async mode picked by installed deps (eventlet/gevent/threading)
    # For Render: ensure eventlet or gevent is installed and set in start cmd.

def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)
    jwt.init_app(app)

    # Limiter: use configured backend if present
    storage_uri = app.config.get("RATELIMIT_STORAGE_URI")
    limiter._storage_uri = storage_uri  # set at runtime if provided
    limiter._default_limits = DEFAULT_LIMITS
    limiter.init_app(app)

    # OAuth providers can be configured via env (example placeholders)
    oauth.init_app(app)
    # Example:
    # oauth.register(
    #     name="google",
    #     client_id=os.getenv("OAUTH_CLIENT_ID"),
    #     client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
    #     access_token_url=os.getenv("OAUTH_TOKEN_URL"),
    #     authorize_url=os.getenv("OAUTH_AUTH_URL"),
    #     api_base_url=os.getenv("OAUTH_USERINFO_URL"),
    #     client_kwargs={"scope": "openid email profile"},
    # )

    # SocketIO is initialized after blueprints (to avoid circular imports)
    # socketio.init_app(app) is called at the end of create_app()

def _register_blueprints(app: Flask) -> None:
    """
    Import and register all blueprints declared as `bp` inside erp.routes.* modules.
    """
    routes_pkg = "erp.routes"
    # Explicit list for predictability; add/remove modules as needed.
    modules: Iterable[str] = (
        "auth", "main", "admin", "analytics", "api", "crm", "finance",
        "health", "help", "hr", "hr_workflows", "inventory", "kanban",
        "manufacturing", "orders", "plugins", "privacy", "procurement",
        "projects", "receive_inventory", "report_builder", "tenders", "webhooks",
        "dashboard_customize",
    )
    for name in modules:
        try:
            mod = import_module(f"{routes_pkg}.{name}")
            bp = getattr(mod, "bp", None)
            if bp is not None:
                app.register_blueprint(bp)
        except Exception as e:
            # Don’t fail boot if a non-critical blueprint misconfigures; log in real app.
            # Use your audit logger here if available.
            pass

def _configure_proxies(app: Flask) -> None:
    # For Render / reverse proxies
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)  # type: ignore[attr-defined]

def _secure_headers(app: Flask) -> None:
    @app.after_request
    def _set_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault("X-XSS-Protection", "0")
        # Add CSP/COOP/COEP/CORP per your policy if not already templated
        return resp

def create_app() -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )

    # Ensure instance folder
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    _load_config(app)
    _init_extensions(app)
    _configure_proxies(app)
    _secure_headers(app)

    _register_blueprints(app)

    # Root -> login chooser (template exists at templates/choose_login.html)
    @app.get("/")
    def _root():
        return redirect(url_for("auth.choose_login"))

    # SocketIO last
    socketio.init_app(app)

    return app
