import os
import importlib
import pkgutil
from datetime import date
from typing import Any

from flask import Flask, render_template, Blueprint

# Extensions (defined in erp/extensions.py)
from .extensions import db, login_manager, csrf


def _register_blueprints(app: Flask) -> None:
    """
    Auto-discover and register all Flask Blueprints in erp.routes.*
    A module qualifies if it defines at least one flask.Blueprint object.
    """
    import erp.routes as routes_pkg  # noqa: WPS433 (import inside function is intentional)

    # Walk immediate submodules in erp.routes
    for _finder, module_short_name, _ispkg in pkgutil.iter_modules(routes_pkg.__path__):
        module_fqn = f"{routes_pkg.__name__}.{module_short_name}"
        module = importlib.import_module(module_fqn)

        # Register any Blueprint objects defined in the module
        for obj in module.__dict__.values():
            if isinstance(obj, Blueprint):
                app.register_blueprint(obj)


def _load_default_config(app: Flask) -> None:
    """
    Minimal, safe defaults. Environment can override these on Render.
    """
    # SECRET_KEY
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))

    # Database
    db_url = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")
    # Render can still supply legacy postgres:// — normalize for SQLAlchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", db_url)
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Misc sensible defaults
    app.config.setdefault("PREFERRED_URL_SCHEME", os.getenv("PREFERRED_URL_SCHEME", "https"))
    app.config.setdefault("SESSION_COOKIE_SECURE", os.getenv("SESSION_COOKIE_SECURE", "true").lower() in {"1", "true", "yes"})
    app.config.setdefault("SESSION_COOKIE_SAMESITE", os.getenv("SESSION_COOKIE_SAMESITE", "Lax"))


def create_app(config_object: Any | None = None) -> Flask:
    """
    App factory. Keeps side-effects to a minimum and avoids importing anything
    that could require a request context at import time.
    """
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # 1) Load config (defaults first, then optional override)
    _load_default_config(app)
    if config_object is not None:
        app.config.from_object(config_object)

    # 2) Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # 3) Jinja context/globals
    @app.context_processor
    def inject_globals():
        # Provide a stable `current_year` for templates (fixes footer error)
        return {"current_year": date.today().year}

    # 4) Health endpoint (used by Render)
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    # 5) Error handlers
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404 if os.path.exists(os.path.join(app.template_folder, "errors", "404.html")) else ("Not Found", 404)

    @app.errorhandler(500)
    def server_error(_e):
        # Keep it extremely safe: render our template if present, otherwise plain text.
        template_path = os.path.join(app.template_folder, "errors", "500.html")
        if os.path.exists(template_path):
            return render_template("errors/500.html"), 500
        return "Internal Server Error", 500

    # 6) Register all blueprints from erp.routes.*
    _register_blueprints(app)

    # Make `/foo` and `/foo/` both work
    app.url_map.strict_slashes = False

    return app
