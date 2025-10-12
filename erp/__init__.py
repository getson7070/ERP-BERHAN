# erp/__init__.py
import datetime
import importlib
import os
import pkgutil
from flask import Flask, render_template
from .extensions import init_app_extensions, db, login_manager, csrf, limiter, socketio

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Core config
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "change-me"))
    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI",
        os.environ.get("DATABASE_URL", "sqlite:///berhan.sqlite3").replace("postgres://", "postgresql://")
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("JSON_SORT_KEYS", False)
    app.config.setdefault("SEND_FILE_MAX_AGE_DEFAULT", 0)

    # Extensions
    init_app_extensions(app)

    # Brand + year for templates
    @app.context_processor
    def inject_brand_and_year():
        return {
            "brand_name": os.environ.get("BRAND_NAME", "BERHAN"),
            "brand_primary": os.environ.get("BRAND_PRIMARY", "#0f6ab5"),
            "brand_logo": os.environ.get("BRAND_LOGO", "pictures/BERHAN-PHARMA-LOGO.jpg"),
            "current_year": datetime.datetime.utcnow().year,
        }

    # Healthcheck
    @app.get("/health")
    def health():
        return {"ok": True}, 200

    # Errors
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        try:
            return render_template("errors/500.html"), 500
        except Exception:
            return ("Internal Server Error", 500)

    _register_blueprints(app)
    return app

def _register_blueprints(app):
    """Autoload blueprints from erp.routes.*; skip modules that fail import."""
    from . import routes as routes_pkg
    for _, module_name, is_pkg in pkgutil.iter_modules(routes_pkg.__path__):
        if is_pkg or module_name.startswith("_"):
            continue
        module_fqn = f"{routes_pkg.__name__}.{module_name}"
        try:
            module = importlib.import_module(module_fqn)
        except Exception as exc:
            app.logger.warning("Skipping routes module %s due to import error: %s", module_fqn, exc)
            continue

        bp = getattr(module, "bp", None)
        if bp is None:
            for attr in dir(module):
                if attr.endswith("_bp"):
                    bp = getattr(module, attr)
                    break

        if bp is not None:
            try:
                app.register_blueprint(bp)
                app.logger.info("Registered blueprint from %s", module_fqn)
            except Exception as exc:
                app.logger.warning("Failed to register blueprint from %s: %s", module_fqn, exc)
        else:
            app.logger.debug("No blueprint found in %s", module_fqn)

__all__ = ["create_app", "db", "login_manager", "csrf", "limiter", "socketio"]
