# erp/__init__.py
import os
import pkgutil
import importlib
from datetime import datetime
from flask import Flask, render_template, g

from .extensions import db, login_manager, csrf, limiter, socketio, init_extensions

def _default_config(app: Flask):
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("BRAND_NAME", os.getenv("BRAND_NAME", "BERHAN"))
    app.config.setdefault("BRAND_PRIMARY_COLOR", os.getenv("BRAND_PRIMARY_COLOR", "#005aa7"))
    app.config.setdefault("BRAND_LOGO_PATH", os.getenv("BRAND_LOGO_PATH", "pictures/BERHAN-PHARMA-LOGO.jpg"))
    # If Alembic didn’t create new tables yet, we’ll ensure they exist to prevent crashes.
    app.config.setdefault("AUTO_CREATE_TABLES", True)
    # Useful for health checks
    app.config.setdefault("HEALTH_OK_TEXT", "OK")

def _register_blueprints(app: Flask):
    """Auto-register all blueprints under erp.routes.*.
    Will LOG and SKIP routes that fail to import to avoid taking down the app."""
    routes_pkg = importlib.import_module("erp.routes")
    for module_info in pkgutil.iter_modules(routes_pkg.__path__):
        module_fqn = f"{routes_pkg.__name__}.{module_info.name}"
        try:
            module = importlib.import_module(module_fqn)
        except Exception as e:
            app.logger.error("Failed importing %s: %r", module_fqn, e)
            continue

        # find any Flask Blueprint instances exposed by the module
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            # duck-type check to avoid importing Flask here
            if getattr(obj, "name", None) and getattr(obj, "register", None):
                # looks like a blueprint
                try:
                    app.register_blueprint(obj)
                    app.logger.info("Registered blueprint from %s: %s", module_fqn, obj.name)
                except Exception as e:
                    app.logger.error("Failed registering blueprint %s: %r", module_fqn, e)

def _register_error_pages(app: Flask):
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

def _context_processors(app: Flask):
    @app.context_processor
    def inject_brand_and_year():
        return {
            "brand_name": app.config.get("BRAND_NAME"),
            "brand_primary_color": app.config.get("BRAND_PRIMARY_COLOR"),
            "brand_logo_path": app.config.get("BRAND_LOGO_PATH"),
            "current_year": datetime.utcnow().year,
        }

    # A very light global to help nav decide visibility in templates that choose to use it.
    @app.before_request
    def _set_default_activation():
        # Avoid template errors if a page doesn’t pass activation explicitly
        g.activation = getattr(g, "activation", {}) or {}

def _ensure_tables(app: Flask):
    if app.config.get("AUTO_CREATE_TABLES"):
        try:
            with app.app_context():
                db.create_all()
        except Exception as e:
            app.logger.warning("db.create_all() failed (non-fatal): %r", e)

def create_app(config_object=None) -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/static",
        template_folder="templates",
    )

    _default_config(app)

    if config_object:
        app.config.from_object(config_object)
    # Allow env-based overrides (Render etc.)
    if os.getenv("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

    # Init extensions
    init_extensions(app)

    # CRITICAL: register Flask-Login loader early so current_user is safe in templates
    try:
        from .auth import user_loader as _user_loader  # noqa: F401
    except Exception as e:
        app.logger.error("Failed to import auth.user_loader: %r", e)

    _register_error_pages(app)
    _context_processors(app)
    _register_blueprints(app)
    _ensure_tables(app)

    app.logger.info("ERP app created. Brand=%s", app.config.get("BRAND_NAME"))
    return app
