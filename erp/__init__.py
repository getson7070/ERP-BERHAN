# erp/__init__.py
from __future__ import annotations

import importlib
import os
from datetime import datetime
from typing import Optional

from flask import Flask, render_template
from .extensions import (
    db,
    migrate,
    login_manager,
    cors,
    cache,
    mail,
    socketio,
    limiter,
)

def create_app(config_object: Optional[str] = None) -> Flask:
    """
    Application factory.
    """
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # ---------------------------
    # Basic configuration
    # ---------------------------
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "change-me"))
    # Render provides DATABASE_URL. SQLAlchemy prefers postgresql+psycopg2://
    db_uri = os.environ.get("DATABASE_URL")
    if db_uri and db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", db_uri or "sqlite:///app.db")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Branding
    app.config.setdefault("BRAND_NAME", os.environ.get("BRAND_NAME", "BERHAN"))
    app.config.setdefault("BRAND_PRIMARY", os.environ.get("BRAND_PRIMARY", "#17468B"))
    app.config.setdefault("BRAND_ACCENT", os.environ.get("BRAND_ACCENT", "#00AEEF"))

    # Limiter storage (avoid prod warning)
    # If REDIS_URL is set, Flask-Limiter will use it; otherwise memory://
    app.config.setdefault(
        "RATELIMIT_STORAGE_URI", os.environ.get("REDIS_URL", "memory://")
    )

    # Optional external config override
    if config_object:
        app.config.from_object(config_object)

    # ---------------------------
    # Init extensions
    # ---------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})
    mail.init_app(app)
    limiter.init_app(app)

    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Flask-SocketIO (eventlet is configured in wsgi.py/gunicorn)
    socketio.init_app(app, cors_allowed_origins="*")

    # ---------------------------
    # Template context
    # ---------------------------
    @app.context_processor
    def inject_brand():
        return {
            "brand_name": app.config["BRAND_NAME"],
            "brand_primary": app.config["BRAND_PRIMARY"],
            "brand_accent": app.config["BRAND_ACCENT"],
            "current_year": datetime.utcnow().year,
        }

    # ---------------------------
    # Error handlers
    # ---------------------------
    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_):
        return render_template("errors/500.html"), 500

    # ---------------------------
    # Blueprints
    # ---------------------------
    _register_blueprints(app)

    # Ensure Flask-Login loaders are registered
    # (auth_loaders.py ties into the shared login_manager instance)
    from . import auth_loaders as _  # noqa: F401

    return app


def _register_blueprints(app: Flask) -> None:
    """
    Dynamically import modules under erp.routes.* and register any "bp" blueprint.
    """
    import pkgutil
    from . import routes as routes_pkg

    for modinfo in pkgutil.iter_modules(routes_pkg.__path__):
        module_fqn = f"{routes_pkg.__name__}.{modinfo.name}"
        module = importlib.import_module(module_fqn)
        bp = getattr(module, "bp", None)
        if bp is not None:
            app.register_blueprint(bp)
