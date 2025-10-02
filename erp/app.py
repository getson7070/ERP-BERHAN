# erp/app.py
from __future__ import annotations

import importlib
import pkgutil
from typing import Optional

from flask import Flask, jsonify
from .extensions import init_extensions


def _register_blueprints(app: Flask, package_name: str = "erp.routes") -> None:
    """Auto-register any module in `erp.routes` that exposes `bp` (a Blueprint)."""
    try:
        package = importlib.import_module(package_name)
    except ModuleNotFoundError:
        return

    for _, modname, ispkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        if ispkg:
            continue
        try:
            module = importlib.import_module(modname)
        except Exception as exc:
            app.logger.warning("Skipping %s due to import error: %s", modname, exc)
            continue

        bp = getattr(module, "bp", None)
        if bp is None:
            continue

        # Avoid duplicate names
        if bp.name in app.blueprints:
            app.logger.info("Blueprint %s already registered; skipping.", bp.name)
            continue

        url_prefix = getattr(module, "URL_PREFIX", None)
        app.register_blueprint(bp, url_prefix=url_prefix)


def create_app(config_object: Optional[str] = None) -> Flask:
    app = Flask(__name__)

    # Basic secrets / settings from environment if provided
    app.config.setdefault("SECRET_KEY",        __import__("os").getenv("FLASK_SECRET_KEY", "change-me"))
    app.config.setdefault("JWT_SECRET_KEY",    __import__("os").getenv("JWT_SECRET"))
    app.config.setdefault("JSON_SORT_KEYS", False)

    # Initialize all extensions (DB, CORS, Cache, Limiter, etc.)
    init_extensions(app)

    # Auto-add blueprints in erp.routes
    _register_blueprints(app)

    # Health + root
    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/")
    def index():
        return jsonify(status="ready", note="ERP backend API")

    return app
