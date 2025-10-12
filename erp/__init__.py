import logging
import os
import importlib
import inspect
import pkgutil
from datetime import datetime

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Basic config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # Jinja helper to check endpoint existence in templates
    def has_endpoint(endpoint: str) -> bool:
        return endpoint in app.view_functions
    app.jinja_env.globals["has_endpoint"] = has_endpoint

    # Make current year available to all templates
    @app.context_processor
    def inject_now():
        return {"current_year": datetime.utcnow().year}

    # Error pages (base.html is defensive now)
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    _register_blueprints(app)
    return app


def _register_blueprints(app: Flask) -> None:
    """Import every module in erp.routes and register any Blueprint objects found.
    Errors in one module are logged but do NOT block others."""
    import erp.routes as routes_pkg
    logger = app.logger or logging.getLogger(__name__)

    for _, module_name, ispkg in pkgutil.iter_modules(routes_pkg.__path__):
        if ispkg or module_name.startswith("_"):
            continue
        full_name = f"{routes_pkg.__name__}.{module_name}"
        try:
            module = importlib.import_module(full_name)
        except Exception:
            logger.exception("Failed importing %s; continuing without it.", full_name)
            continue

        from flask import Blueprint
        for _, obj in inspect.getmembers(module):
            if isinstance(obj, Blueprint):
                try:
                    app.register_blueprint(obj)
                    logger.info("Registered blueprint '%s' from %s", obj.name, full_name)
                except Exception:
                    logger.exception("Failed registering blueprint from %s", full_name)
                    continue
