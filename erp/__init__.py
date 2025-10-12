import logging
import os
import importlib
import inspect
import pkgutil
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ---- Config ----
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ---- Extensions ----
    db.init_app(app)
    migrate.init_app(app, db)

    # ---- Jinja helper: guard against missing endpoints in templates ----
    def has_endpoint(endpoint: str) -> bool:
        return endpoint in app.view_functions

    app.jinja_env.globals["has_endpoint"] = has_endpoint

    # ---- Health endpoints (both /healthz and /health) ----
    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    # ---- Error handlers (render simple templates; base.html is now defensive) ----
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        # Render a friendly page; details are in logs
        return render_template("errors/500.html"), 500

    # ---- Register blueprints from erp.routes robustly ----
    _register_blueprints(app)

    return app


def _register_blueprints(app: Flask) -> None:
    """
    Import every module in erp.routes and register any Flask Blueprint objects
    found there. Errors in one module are logged but do NOT block the rest.
    """
    import erp.routes as routes_pkg
    logger = app.logger or logging.getLogger(__name__)

    for finder, module_name, ispkg in pkgutil.iter_modules(routes_pkg.__path__):
        if ispkg or module_name.startswith("_"):
            continue
        full_name = f"{routes_pkg.__name__}.{module_name}"
        try:
            module = importlib.import_module(full_name)
        except Exception:
            logger.exception("Failed importing %s; continuing without it.", full_name)
            continue

        # Register any Blueprint objects defined in the module
        for _, obj in inspect.getmembers(module):
            try:
                from flask import Blueprint  # local import to avoid hard dependency here
                if isinstance(obj, Blueprint):
                    app.register_blueprint(obj)
                    logger.info("Registered blueprint '%s' from %s", obj.name, full_name)
            except Exception:
                logger.exception("Failed registering blueprint from %s", full_name)
                continue
