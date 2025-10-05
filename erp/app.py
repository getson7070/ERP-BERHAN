# erp/app.py
from __future__ import annotations

import logging
import os
from flask import Flask
from flask_cors import CORS

from .extensions import db, migrate, cache, limiter, login_manager
from .web import web_bp
# import the alias we added; this also works as: `from erp.routes.auth import bp as auth_bp`
from .routes.auth import auth_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    # ---- Config ----
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Cache (SimpleCache by default via env you set)
    app.config["CACHE_TYPE"] = os.getenv("CACHE_TYPE", "SimpleCache")
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))

    # CORS
    CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

    # ---- Extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    # Limiter with env override e.g. "300 per minute; 30 per second"
    default_limits = os.getenv("DEFAULT_RATE_LIMITS", "200 per minute")
    limiter.default_limits = [s.strip() for s in default_limits.split(";") if s.strip()]
    limiter.init_app(app)

    login_manager.init_app(app)

    # ---- Blueprints ----
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)

    # If you want to auto-load all other route modules later, add:
    # _register_remaining_blueprints(app)

    # ---- Logging ----
    logging.basicConfig(level=os.getenv("LOGLEVEL", "INFO"))

    return app


# Optional auto-discovery if/when you’re ready to wire every routes/*.py module
def _register_remaining_blueprints(app: Flask) -> None:
    """
    Discover & register all Flask Blueprints found under `erp.routes.*`.
    Skips already-registered names and avoids crashes if a module imports fail.
    """
    import importlib, pkgutil
    from flask import Blueprint

    seen = set(app.blueprints.keys())
    try:
        import erp.routes as routes_pkg
    except Exception as e:
        app.logger.warning("Couldn't import erp.routes: %s", e)
        return

    for modinfo in pkgutil.iter_modules(routes_pkg.__path__, routes_pkg.__name__ + "."):
        try:
            mod = importlib.import_module(modinfo.name)
        except Exception as e:
            app.logger.warning("[blueprints] failed to import %s: %s", modinfo.name, e)
            continue

        for attr_name, obj in vars(mod).items():
            if isinstance(obj, Blueprint) and obj.name not in seen:
                app.register_blueprint(obj)
                seen.add(obj.name)
                app.logger.info("[blueprints] registered %s from %s.%s", obj.name, modinfo.name, attr_name)
