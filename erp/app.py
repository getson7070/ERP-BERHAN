# erp/app.py
from __future__ import annotations

import importlib
import os
import pkgutil
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, redirect, url_for
from flask import Blueprint
from werkzeug.routing import BuildError

from .extensions import (
    db,
    migrate,
    oauth,
    limiter,
    cors,
    cache,
    compress,
    csrf,
    babel,
    jwt,
    socketio,
    init_extensions,
)


def _coerce_db_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    scheme = url.split("://", 1)[0]
    if scheme == "postgresql" and "+psycopg2" not in scheme:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def _configure_defaults(app: Flask) -> None:
    # Secrets (override via env in prod)
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "replace-me"))
    app.config.setdefault("JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "replace-me-too"))

    # CORS
    app.config.setdefault("CORS_ORIGINS", os.getenv("CORS_ORIGINS", "*"))

    # Rate limiting backend & defaults
    app.config.setdefault("RATELIMIT_STORAGE_URI", os.getenv("RATELIMIT_STORAGE_URI", "memory://"))
    app.config.setdefault("RATELIMIT_DEFAULT", os.getenv("RATELIMIT_DEFAULT", "60 per minute"))

    # Cache
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")))

    # Socket.IO message queue (optional)
    mq = os.getenv("SOCKETIO_MESSAGE_QUEUE") or os.getenv("REDIS_URL")
    if mq:
        app.config["SOCKETIO_MESSAGE_QUEUE"] = mq

    # Database: accept either SQLALCHEMY_DATABASE_URI or DATABASE_URL
    raw_url = app.config.get("SQLALCHEMY_DATABASE_URI") or os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    final_url = _coerce_db_url(raw_url)
    if not final_url:
        raise RuntimeError("Either 'SQLALCHEMY_DATABASE_URI' or 'DATABASE_URL' must be set.")
    app.config["SQLALCHEMY_DATABASE_URI"] = final_url
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)


def _maybe_register_blueprint(app: Flask, bp: Blueprint, *, url_prefix: Optional[str] = None) -> None:
    if bp.name in app.blueprints:
        app.logger.info("Skipping duplicate blueprint registration: %s", bp.name)
        return
    app.register_blueprint(bp, url_prefix=url_prefix)


def _auto_register_blueprints(app: Flask) -> None:
    """
    Auto-import and register blueprints from erp.routes.* modules.
    Each module may export `bp` or `blueprint` (Flask Blueprint).
    Optional: URL_PREFIX/url_prefix variable for prefix.
    """
    package_name = "erp.routes"
    try:
        pkg = importlib.import_module(package_name)
    except ModuleNotFoundError:
        app.logger.info("No routes package found at %s; skipping auto-registration.", package_name)
        return

    package_path = Path(pkg.__file__).parent
    for module_info in pkgutil.iter_modules([str(package_path)]):
        mod_name = f"{package_name}.{module_info.name}"
        module = importlib.import_module(mod_name)

        bp = getattr(module, "bp", None) or getattr(module, "blueprint", None)
        if isinstance(bp, Blueprint):
            url_prefix = getattr(module, "URL_PREFIX", None) or getattr(module, "url_prefix", None)
            _maybe_register_blueprint(app, bp, url_prefix=url_prefix)


def _install_fallback_home_if_missing(app: Flask) -> None:
    if "home" in app.view_functions:
        return

    @app.get("/home")
    def home():  # endpoint name = 'home'
        try:
            return redirect(url_for("health"))
        except BuildError:
            return jsonify({"status": "ok", "page": "home"}), 200


def _install_health_and_root(app: Flask) -> None:
    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/")
    def _root():
        # Try likely endpoints in order; fall back to health.
        for endpoint in ("auth.login", "auth.choose_login", "home", "health"):
            try:
                return redirect(url_for(endpoint))
            except BuildError:
                continue
        return jsonify({"status": "ok"}), 200


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    _configure_defaults(app)
    init_extensions(app)           # DB, migrate, oauth, limiter, cors, cache, compress, csrf, babel, jwt, socketio
    _auto_register_blueprints(app) # Avoid duplicates
    _install_health_and_root(app)
    _install_fallback_home_if_missing(app)

    # Shell ctx convenience
    @app.shell_context_processor
    def _make_shell_context():
        return {"app": app, "db": db}

    return app
