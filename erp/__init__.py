# erp/__init__.py
from __future__ import annotations

import importlib
import logging
import os
from datetime import datetime
from typing import Iterable

from flask import Flask, render_template, url_for

from .config import get_config_obj
from .extensions import (
    db,
    migrate,
    login_manager,
    mail,
    cache,
    cors,
    limiter,
    socketio,
    init_extensions,
)

# --------- logging ----------
log = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOGLEVEL", "INFO"))


def _safe_import_and_register(app: Flask, module_fqn: str) -> bool:
    """
    Try to import a routes module and register its blueprint.
    The module must expose `bp` or `<name>_bp` (Blueprint).
    Returns True on success, False if skipped (and logs the reason).
    """
    try:
        module = importlib.import_module(module_fqn)
    except Exception as e:
        app.logger.exception("Skipping routes module %s (import error): %s", module_fqn, e)
        return False

    bp = getattr(module, "bp", None)
    if bp is None:
        # also try <module_name>_bp convention
        name = module_fqn.rsplit(".", 1)[-1]
        bp = getattr(module, f"{name}_bp", None)

    if bp is None:
        app.logger.warning("Skipping %s: no blueprint `bp` or `%s_bp` found.", module_fqn, module_fqn.rsplit(".", 1)[-1])
        return False

    try:
        app.register_blueprint(bp)
        app.logger.info("Registered blueprint from %s", module_fqn)
        return True
    except Exception as e:
        app.logger.exception("Failed to register blueprint from %s: %s", module_fqn, e)
        return False


def _register_blueprints(app: Flask) -> None:
    """
    Register only the stable/needed blueprints.
    Modules that fail to import or register will be logged and skipped,
    so one bad module cannot take the whole app down.
    """
    modules: Iterable[str] = [
        # entry + public pages
        "erp.routes.main",
        "erp.routes.feedback",
        "erp.routes.privacy",
        "erp.routes.help",
        "erp.routes.health",

        # core features that exist in this repo
        "erp.routes.api",
        "erp.routes.analytics",
        "erp.routes.inventory",
        "erp.routes.orders",
        "erp.routes.dashboard_customize",

        # DO NOT enable hr module until an Employee model exists.
        # "erp.routes.hr",
    ]

    for module_fqn in modules:
        _safe_import_and_register(app, module_fqn)


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # 1) Load config first
    cfg_string = os.getenv("FLASK_CONFIG", "erp.config.ProductionConfig")
    app.config.from_object(get_config_obj(cfg_string))

    # 2) Initialize extensions (creates limiter, login_manager, db, etc.)
    init_extensions(app)

    # 3) Register blueprints safely
    _register_blueprints(app)

    # 4) Jinja + context helpers (brand, year, etc.)
    @app.context_processor
    def inject_brand():
        brand_name = app.config.get("BRAND_NAME", "Berhan Pharma")
        logo_path = app.config.get("BRAND_LOGO_PATH", "pictures/BERHAN-PHARMA-LOGO.jpg")
        brand_primary = app.config.get("BRAND_PRIMARY_COLOR", "#0a7e5c")
        return {
            "brand_name": brand_name,
            "brand_logo_url": url_for("static", filename=logo_path),
            "brand_primary": brand_primary,
            "current_year": datetime.utcnow().year,
        }

    # 5) Simple error pages that won’t crash due to Jinja issues
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        # Do NOT raise here—return a simple, resilient page
        return render_template("errors/500.html"), 500

    return app
