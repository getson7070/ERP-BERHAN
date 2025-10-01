# erp/app.py  (FULL REPLACEMENT)

from __future__ import annotations

import os
import logging
import importlib
import pkgutil
from typing import Optional

from flask import Flask, redirect, url_for, jsonify

# Import extensions WITHOUT touching jwt proxies at import time
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
    socketio,
    init_extensions,
)

# -----------------------------------------------------------------------------
# Configuration helpers
# -----------------------------------------------------------------------------

def _normalize_pg_uri(uri: str) -> str:
    """Ensure the URI is psycopg2-flavored and has sslmode=require."""
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql+psycopg2://", 1)
    elif uri.startswith("postgresql://") and "+psycopg2" not in uri:
        uri = uri.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "sslmode=" not in uri:
        uri += ("&" if "?" in uri else "?") + "sslmode=require"
    return uri


def _configure_sqlalchemy(app: Flask) -> None:
    """
    Force SQLALCHEMY_DATABASE_URI from environment (Render).
    Called AFTER any app.config.from_* so we don't accidentally overwrite it later.
    """
    # Preferred precedence order
    raw_uri = (
        os.getenv("SQLALCHEMY_DATABASE_URI")
        or os.getenv("INTERNAL_DATABASE_URL")  # Render internal URL (if you added it)
        or os.getenv("DATABASE_URL")
    )

    if not raw_uri:
        # Nothing to do; Flask-SQLAlchemy will error if truly absent.
        app.logger.warning("No DB URI found in env (SQLALCHEMY_DATABASE_URI / DATABASE_URL).")
        return

    uri = _normalize_pg_uri(raw_uri)
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    # Sensible default to quiet warnings
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Minimal visibility without leaking secrets
    try:
        host_port = uri.split("@", 1)[1].split("/", 1)[0]
    except Exception:
        host_port = "<hidden>"
    app.logger.info("SQLAlchemy configured (host: %s)", host_port)


# -----------------------------------------------------------------------------
# Blueprint auto-registration with duplicate guard
# -----------------------------------------------------------------------------

def _maybe_register_blueprint(app: Flask, module_name: str, url_prefix: Optional[str] = None) -> None:
    """
    Import a module, look for a Blueprint object, and register it only once.
    Common attribute names are checked. If already registered, do nothing.
    """
    mod = importlib.import_module(module_name)

    for attr in ("bp", "blueprint", "bp_auth", "auth_bp"):
        bp = getattr(mod, attr, None)
        if bp is None:
            continue

        # Skip duplicates
        if bp.name in app.blueprints:
            return

        final_prefix = url_prefix if url_prefix is not None else f"/{bp.name}"
        app.register_blueprint(bp, url_prefix=final_prefix)
        return  # registered successfully


def _auto_register_blueprints(app: Flask, package: str = "erp") -> None:
    """
    Walk the package and auto-register blueprints from modules ending
    with '.routes' or '.views'.
    """
    base_pkg = importlib.import_module(package)
    for _, name, _ in pkgutil.walk_packages(base_pkg.__path__, base_pkg.__name__ + "."):
        if name.endswith(".routes") or name.endswith(".views"):
            _maybe_register_blueprint(app, name)


# -----------------------------------------------------------------------------
# App factory
# -----------------------------------------------------------------------------

def create_app() -> Flask:
    app = Flask(__name__)

    # --- Load any of your existing config here, if you have it ---
    # Example (keep or remove if you don't use them):
    # app.config.from_object("erp.config.Production")  # if you have a config module
    # app.config.from_prefixed_env()  # copies FLASK_* into config (optional)

    # Always enforce DB config from environment AFTER any from_* calls
    _configure_sqlalchemy(app)

    # Optional defaults to silence warnings (safe in any env)
    app.config.setdefault("CACHE_TYPE", "null")  # or "simple" / RedisCache
    app.config.setdefault("RATELIMIT_STORAGE_URI", "memory://")  # set a Redis URI in prod

    # Initialize all extensions (this will lazily import JWTManager inside)
    init_extensions(app)

    # Register blueprints, but never double-register the same name
    _auto_register_blueprints(app, package="erp")

    # --- Base routes ---
    @app.route("/", methods=["GET", "HEAD"])
    def _root():
        # Prefer 'auth.login' if present, otherwise show a simple health-like landing
        try:
            return redirect(url_for("auth.login"))
        except Exception:
            return jsonify({"status": "ok", "message": "ERP backend"}), 200
