from __future__ import annotations

import importlib
import os
import pkgutil
from typing import Iterable, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from flask import Blueprint, Flask, jsonify, redirect, url_for

from .extensions import (
    babel,
    cache,
    compress,
    cors,
    db,
    init_extensions,
    limiter,
    migrate,
    oauth,
    socketio,
)

DEFAULT_CONFIG: dict = {
    "JSON_SORT_KEYS": False,
    "JSONIFY_PRETTYPRINT_REGULAR": False,
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
}


def _normalize_pg_uri(raw: str) -> str:
    """
    Normalize various Postgres URL shapes to something SQLAlchemy likes.
    - postgres:// -> postgresql+psycopg2://
    - ensure sslmode=require for remote hosts if not specified
    """
    if not raw:
        return raw

    uri = raw.strip()

    # Old Heroku style
    if uri.startswith("postgres://"):
        uri = "postgresql+psycopg2://" + uri[len("postgres://") :]

    # If user gave plain 'postgresql://' (no driver), it's still fine for SQLAlchemy,
    # but we prefer being explicit:
    if uri.startswith("postgresql://"):
        uri = "postgresql+psycopg2://" + uri[len("postgresql://") :]

    try:
        parsed = urlparse(uri)
        # Decide whether to force sslmode=require
        is_local = parsed.hostname in (None, "localhost", "127.0.0.1") or (
            parsed.hostname and parsed.hostname.endswith(".internal")
        )

        # Append sslmode=require if not local and not already set
        q = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if not is_local and "sslmode" not in q:
            q["sslmode"] = "require"

        new_query = urlencode(q)
        uri = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )
    except Exception:
        # If parsing fails, return best-effort string
        return uri

    return uri


def _load_db_uri_from_env() -> Optional[str]:
    """
    Prefer app-specific var, then common Render/Heroku-style names.
    """
    for key in (
        "SQLALCHEMY_DATABASE_URI",
        "DATABASE_URL",
        "INTERNAL_DATABASE_URL",
        "POSTGRES_URL",
        "POSTGRESQL_URL",
    ):
        val = os.getenv(key)
        if val:
            return _normalize_pg_uri(val)
    return None


def _maybe_register_blueprint(
    app: Flask, module_name: str, url_prefix: Optional[str] = None
) -> Optional[Blueprint]:
    """Import module_name and, if it exposes a 'bp' (Blueprint), register it."""
    try:
        mod = importlib.import_module(module_name)
    except Exception:
        return None
    bp = getattr(mod, "bp", None)
    if isinstance(bp, Blueprint):
        app.register_blueprint(bp, url_prefix=url_prefix)
        return bp
    return None


def _iter_package_modules(package_name: str) -> Iterable[str]:
    """Yield importable module names inside a package."""
    try:
        pkg = importlib.import_module(package_name)
    except Exception:
        return []
    if not hasattr(pkg, "__path__"):
        return []
    for info in pkgutil.iter_modules(pkg.__path__, package_name + "."):
        yield info.name


def _auto_register_blueprints(app: Flask) -> None:
    """
    Register blueprints from our known locations.
    Supports both:
      - erp.routes.<module>
      - erp.blueprints.<module>
    """
    # Explicit, common ones
    for name in (
        "erp.routes.health",
        "erp.routes.auth",
        "erp.routes.api",
        "erp.blueprints.inventory",
    ):
        _maybe_register_blueprint(app, name)

    # Dynamic discovery
    for pkg in ("erp.routes", "erp.blueprints"):
        for module_name in _iter_package_modules(pkg):
            _maybe_register_blueprint(app, module_name)


def create_app(config: Optional[dict] = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.update(DEFAULT_CONFIG)

    # Secrets & CORS
    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY", app.config.get("SECRET_KEY", "change-me")
    )
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    if cors_origins:
        app.config["CORS_ORIGINS"] = cors_origins

    # Database URI (from env, normalized)
    db_uri = _load_db_uri_from_env()
    if db_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    else:
        # Keep a friendly error if not configured
        # (Flask-SQLAlchemy will also raise, but this message is clearer)
        app.logger.warning(
            "No database URL found. Set SQLALCHEMY_DATABASE_URI or DATABASE_URL."
        )

    # Optional external config last
    if config:
        app.config.update(config)

    # Init all extensions (JWT initialized lazily in init_extensions)
    init_extensions(app)

    # Register blueprints we can find
    _auto_register_blueprints(app)

    # Fallback /health if no health blueprint exists
    if "health.health" not in app.view_functions:
        @app.get("/health")
        def _fallback_health():
            return jsonify({"status": "ready"})

    # Root: prefer auth endpoints if present
    @app.route("/", methods=["GET", "HEAD"])
    def _root():
        candidates = ("auth.choose_login", "auth.login", "auth.index")
        for endpoint in candidates:
            if endpoint in app.view_functions:
                return redirect(url_for(endpoint))
        return jsonify(
            {
                "note": "No auth blueprint endpoint found. Expected one of: auth.choose_login, auth.login, auth.index.",
                "status": "ready",
            }
        )

    return app
