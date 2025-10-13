# erp/__init__.py
from __future__ import annotations
import logging, importlib, os, pkgutil, datetime
from flask import Flask, render_template
from .config import get_config
from .extensions import init_extensions

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(get_config())

    # Init Flask extensions
    init_extensions(app)

    # Register blueprints (fault-tolerant)
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

    # Simple health
    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    # Friendly 500 page
    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    return app

def _register_blueprints(app: Flask) -> None:
    """
    Load only healthy blueprints.
    If a module is broken (SyntaxError / ImportError), we log and keep going.
    This prevents one bad route from crashing the whole service.
    """
    logger = logging.getLogger("erp")
    routes_pkg = "erp.routes"

    # Start with the essentials explicitly
    essential = [
        ("erp.routes.main", "main_bp"),     # choose_login, index
        ("erp.routes.auth", "auth_bp"),     # login endpoints
    ]
    for modname, attr in essential:
        try:
            m = importlib.import_module(modname)
            bp = getattr(m, attr, None)
            if bp:
                app.register_blueprint(bp)
                logger.info("Registered blueprint: %s.%s", modname, attr)
        except Exception as e:
            logger.exception("Failed to register %s: %s", modname, e)

    # Best-effort auto-discovery of additional route modules
    try:
        pkg = importlib.import_module(routes_pkg)
        for _, name, ispkg in pkgutil.iter_modules(pkg.__path__, routes_pkg + "."):
            if ispkg:
                continue
            # Avoid double-loading essentials
            if name in {"erp.routes.main", "erp.routes.auth"}:
                continue
            try:
                m = importlib.import_module(name)
                # Look for any Blueprint instances
                for attr in dir(m):
                    obj = getattr(m, attr)
                    if getattr(obj, "name", None) and getattr(obj, "register", None):
                        # crude check for Blueprint
                        from flask import Blueprint
                        if isinstance(obj, Blueprint):
                            app.register_blueprint(obj)
                            logger.info("Registered blueprint: %s.%s", name, attr)
            except Exception as e:
                logger.warning("Skipped broken routes module %s: %s", name, e)
    except Exception as e:
        logging.getLogger("erp").warning("Route auto-discovery failed: %s", e)
