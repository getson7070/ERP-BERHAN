# erp/__init__.py
from __future__ import annotations
import logging
import importlib
import pkgutil
import datetime
from flask import Flask, render_template
from .config import get_config
from .extensions import init_extensions, login_manager  # keep login_manager available


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(get_config())

    # Init Flask extensions (db, migrate, login_manager, limiter, cors, cache, socketio, etc.)
    init_extensions(app)

    # IMPORTANT: ensure user_loader is registered (executes @login_manager.user_loader)
    from . import auth_loaders as _auth_loaders  # noqa: F401

    # Optional: sanity log to confirm loader is in place
    app.logger.info(
        "Login user_loader set? %s",
        getattr(login_manager, "_user_callback", None) is not None,
    )

    # Register blueprints (auth + all others)
    _register_blueprints(app)

    # Branding + convenience vars for all templates
    @app.context_processor
    def inject_brand():
        return {
            "brand_name": app.config.get("BRAND_NAME", "BERHAN"),
            "brand_primary": app.config.get("BRAND_PRIMARY", "#0d6efd"),
            "brand_accent": app.config.get("BRAND_ACCENT", "#198754"),
            "current_year": datetime.datetime.utcnow().year,
        }

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    return app


def _register_blueprints(app: Flask) -> None:
    """
    1) Register essential blueprints explicitly (so core routes always exist).
    2) Auto-discover & register any other Blueprints under erp.routes.*
    """
    logger = logging.getLogger("erp")

    # Register essentials first
    essentials = [
        ("erp.routes.main", "main_bp"),
        ("erp.routes.auth", "auth_bp"),  # provides endpoint: auth.login (role param)
    ]
    for modname, attr in essentials:
        try:
            m = importlib.import_module(modname)
            bp = getattr(m, attr, None)
            if bp:
                app.register_blueprint(bp)
                logger.info("Registered blueprint: %s.%s", modname, attr)
        except Exception as e:
            logger.exception("Failed to register %s: %s", modname, e)

    # Auto-register any additional blueprints in erp.routes.*
    try:
        routes_pkg = importlib.import_module("erp.routes")
        for _finder, modname, ispkg in pkgutil.iter_modules(routes_pkg.__path__, routes_pkg.__name__ + "."):
            if ispkg or modname in {"erp.routes.main", "erp.routes.auth"}:
                continue
            try:
                m = importlib.import_module(modname)
                from flask import Blueprint
                for attr in dir(m):
                    obj = getattr(m, attr)
                    if isinstance(obj, Blueprint):
                        app.register_blueprint(obj)
                        logger.info("Registered blueprint: %s.%s", modname, attr)
            except Exception as e:
                logger.warning("Skipped routes module %s due to error: %s", modname, e)
    except Exception as e:
        logging.getLogger("erp").warning("Route auto-discovery failed: %s", e)
