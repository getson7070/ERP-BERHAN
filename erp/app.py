from __future__ import annotations

import importlib
import os
import pkgutil
from typing import Iterable, Optional

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
}


def _maybe_register_blueprint(app: Flask, module_name: str, url_prefix: Optional[str] = None) -> Optional[Blueprint]:
    """
    Import module_name and, if it exposes a 'bp' (Blueprint), register it.
    Returns the blueprint or None.
    """
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

    We support both:
      - erp.routes.<module>
      - erp.blueprints.<module>
    And we also try a few explicit modules if present.
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

    # Allow env to inject secrets/URLs
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", app.config.get("SECRET_KEY", "change-me"))
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    if cors_origins:
        app.config["CORS_ORIGINS"] = cors_origins

    if config:
        app.config.update(config)

    # Init all extensions (JWT is initialized lazily inside init_extensions)
    init_extensions(app)

    # Register blueprints we can find
    _auto_register_blueprints(app)

    # Fallback /health if no health blueprint exists
    if "health.health" not in app.view_functions:
        @app.get("/health")
        def _fallback_health():
            return jsonify({"status": "ready"})

    # Root: prefer auth endpoints if present; otherwise explain what's available.
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
