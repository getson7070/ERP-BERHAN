import os
import importlib
import pkgutil
from datetime import date
from typing import Any

from flask import Flask, render_template, Blueprint

from .extensions import db, login_manager, csrf, limiter, socketio


def _register_blueprints(app: Flask) -> None:
    import erp.routes as routes_pkg
    for _finder, module_short_name, _ispkg in pkgutil.iter_modules(routes_pkg.__path__):
        module_fqn = f"{routes_pkg.__name__}.{module_short_name}"
        module = importlib.import_module(module_fqn)
        for obj in module.__dict__.values():
            if isinstance(obj, Blueprint):
                app.register_blueprint(obj)


def _load_default_config(app: Flask) -> None:
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))
    db_url = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", db_url)
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("PREFERRED_URL_SCHEME", os.getenv("PREFERRED_URL_SCHEME", "https"))
    app.config.setdefault("SESSION_COOKIE_SECURE", os.getenv("SESSION_COOKIE_SECURE", "true").lower() in {"1", "true", "yes"})
    app.config.setdefault("SESSION_COOKIE_SAMESITE", os.getenv("SESSION_COOKIE_SAMESITE", "Lax"))
    # CORS for SocketIO, if used
    app.config.setdefault("SOCKETIO_CORS", os.getenv("SOCKETIO_CORS", "*"))


def create_app(config_object: Any | None = None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    _load_default_config(app)
    if config_object is not None:
        app.config.from_object(config_object)

    # Init core extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Init optional ones if present
    if limiter is not None:
        limiter.init_app(app)
    if socketio is not None:
        socketio.init_app(app, cors_allowed_origins=app.config["SOCKETIO_CORS"])

    @app.context_processor
    def inject_globals():
        # Use this in templates instead of calling now()/globals()
        return {"current_year": date.today().year}

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    @app.errorhandler(404)
    def not_found(_e):
        tpl = os.path.join(app.template_folder, "errors", "404.html")
        return (render_template("errors/404.html"), 404) if os.path.exists(tpl) else ("Not Found", 404)

    @app.errorhandler(500)
    def server_error(_e):
        tpl = os.path.join(app.template_folder, "errors", "500.html")
        return (render_template("errors/500.html"), 500) if os.path.exists(tpl) else ("Internal Server Error", 500)

    _register_blueprints(app)
    app.url_map.strict_slashes = False
    return app
