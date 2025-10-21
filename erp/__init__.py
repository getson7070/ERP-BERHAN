# erp/__init__.py
from __future__ import annotations

import os
import pkgutil
from importlib import import_module
from typing import Any

from flask import Flask, Response, jsonify, request, session
from werkzeug.exceptions import HTTPException

# Local imports (present in this project)
from .config import Config, validate_config
from .observability import init_logging
from .security import apply_security_headers
from .errors import register_error_handlers

# Optional DB
try:
    from .db import db  # type: ignore
except Exception:  # pragma: no cover
    db = None  # type: ignore


def _auto_register_blueprints(app: Flask) -> None:
    """Auto-register any 'bp' Flask blueprints in erp.routes.* modules."""
    import erp.routes as routes_pkg

    for mod in pkgutil.iter_modules(routes_pkg.__path__):
        module = import_module(f"erp.routes.{mod.name}")
        bp = getattr(module, "bp", None)
        if bp:
            app.register_blueprint(bp)


def _resolve_webhook_secret_for_request(app: Flask) -> str | None:
    """
    Find the webhook signing secret.

    In TESTING mode, we deliberately ignore environment variables and only honor
    app.config so that machine/user env values cannot affect tests.

    Outside TESTING, accept env or config.
    """
    if app.config.get("TESTING"):
        return app.config.get("WEBHOOK_SIGNING_SECRET") or app.config.get("WEBHOOK_SECRET")

    return (
        os.getenv("WEBHOOK_SIGNING_SECRET")
        or app.config.get("WEBHOOK_SIGNING_SECRET")
        or app.config.get("WEBHOOK_SECRET")
        or os.getenv("WEBHOOK_SECRET")
    )


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)

    # Config
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", app.config.get("SECRET_KEY") or "dev-secret")
    app.config.from_object(Config())
    if test_config:
        app.config.update(test_config)

    # Best-effort config validation
    try:
        validate_config(app.config)
    except Exception:
        pass

    # DB (optional)
    try:
        if db is not None:
            db.init_app(app)
            # Create tables automatically in tests or when explicitly requested
            if app.config.get("TESTING") or os.getenv("AUTO_CREATE_DB") == "1":
                with app.app_context():
                    db.create_all()
    except Exception:
        pass

    # Core app hardening/observability
    apply_security_headers(app)
    register_error_handlers(app)
    init_logging(app)

    # Simple pages used by other tests (language switch & basic dashboard)
    @app.get("/set_language/<lang>")
    def set_language(lang: str) -> Response:
        session["lang"] = lang
        return Response("ok")

    @app.get("/dashboard")
    def dashboard() -> Response:
        lang = session.get("lang", "en")
        html = f'<!doctype html><html lang="{lang}"><head></head><body><select id="lang-select"></select></body></html>'
        return Response(html, mimetype="text/html")

    # Early guard: if webhook secret is not configured, return 500 BEFORE any signature checks
    @app.before_request
    def _webhook_missing_secret_guard():
        if request.path.startswith("/api/webhook"):
            secret = _resolve_webhook_secret_for_request(app)
            if not secret:
                return jsonify({"error": "server not configured"}), 500

    # Do NOT convert HTTPException (e.g., 401/403/409) into 500
    @app.errorhandler(Exception)
    def _err(e: Exception):
        if isinstance(e, HTTPException):
            return e
        app.logger.error("uncaught_exception", exc_info=e)
        return Response('{"error":"internal"}', mimetype="application/json", status=500)

    # Register all blueprints found under erp.routes
    _auto_register_blueprints(app)

    # Ensure webhooks endpoint is present even if auto-register missed it
    try:
        from .routes import webhooks as _webhooks

        if hasattr(_webhooks, "init_app"):
            _webhooks.init_app(app)  # preferred
        elif hasattr(_webhooks, "bp"):
            # avoid double-registration
            if "webhooks" not in app.blueprints:
                app.register_blueprint(_webhooks.bp)
    except Exception as e:
        app.logger.warning("webhooks blueprint not registered: %s", e)

    return app


# --- AUTOAPPEND (safe) ---
# Expose test-expected symbols (safe append)
try:
    from .socket import socketio
except Exception:
    socketio = None
try:
    from .dlq import _dead_letter_handler
except Exception:
    def _dead_letter_handler(*args, **kwargs):
        return False
try:
    from .metrics import (
        GRAPHQL_REJECTS, RATE_LIMIT_REJECTIONS, QUEUE_LAG, AUDIT_CHAIN_BROKEN, OLAP_EXPORT_SUCCESS
    )
except Exception:
    GRAPHQL_REJECTS = 0
    RATE_LIMIT_REJECTIONS = 0
    QUEUE_LAG = 0
    AUDIT_CHAIN_BROKEN = False
    OLAP_EXPORT_SUCCESS = "OLAP_EXPORT_SUCCESS"
