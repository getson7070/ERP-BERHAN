# erp/__init__.py
from __future__ import annotations
import importlib
import logging
import os
from typing import List

from flask import Flask, render_template

from .extensions import db, migrate, login_manager, cache, mail, limiter, socketio
from .config import ProductionConfig, DevelopmentConfig, BaseConfig

LOG = logging.getLogger("erp")
logging.basicConfig(level=logging.INFO)

def _load_config(app: Flask) -> None:
    cfg_path = os.getenv("FLASK_CONFIG", "").strip()
    if cfg_path:
        module, _, name = cfg_path.rpartition(".")
        app.config.from_object(importlib.import_module(module).__dict__[name])
    else:
        # Default to Production if APP_ENV==production; else Dev
        app_env = os.getenv("APP_ENV", "production").lower()
        app.config.from_object(ProductionConfig if app_env == "production" else DevelopmentConfig)

    # If rate limits provided, apply to limiter default limits
    default_limits = app.config.get("DEFAULT_RATE_LIMITS", [])
    if default_limits:
        limiter._default_limits = default_limits  # type: ignore[attr-defined]

def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

    # ---- Flask-Login wiring (fixes "Missing user_loader") ----
    @login_manager.user_loader
    def load_user(user_id: str):
        from erp.models import User  # local import to avoid circulars
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # fallback

def _register_blueprints(app: Flask) -> None:
    """
    Keep the list small & safe-by-default. Optional modules are guarded.
    """
    modules: List[str] = [
        "erp.routes.main",
        "erp.routes.auth",
        # Optional routes may import missing models in your current DB;
        # they are loaded best-effort without breaking the app:
        "erp.routes.analytics",
        "erp.routes.api",
        "erp.routes.dashboard_customize",
        "erp.routes.hr",
        "erp.routes.hr_workflows",
        "erp.routes.inventory",
        "erp.routes.orders",
        "erp.routes.privacy",
        "erp.routes.report_builder",
        "erp.routes.tenders",
    ]
    for module_fqn in modules:
        try:
            module = importlib.import_module(module_fqn)
            bp = getattr(module, "bp", None) or getattr(module, "blueprint", None) or getattr(module, "auth_bp", None)
            if bp is not None:
                app.register_blueprint(bp)
        except Exception as exc:  # non-fatal
            LOG.warning("Skipped routes module %s due to error: %s", module_fqn, exc)

def _inject_branding(app: Flask) -> None:
    @app.context_processor
    def inject_brand():
        return dict(
            brand_name="BERHAN",
            brand_logo="pictures/BERHAN-PHARMA-LOGO.jpg",
            year="2025",
        )

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    _load_config(app)
    _init_extensions(app)
    _register_blueprints(app)
    _inject_branding(app)

    # ---- Error pages ----
    @app.errorhandler(404)
    def not_found(e):  # pragma: no cover
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):  # pragma: no cover
        return render_template("errors/500.html"), 500

    return app
