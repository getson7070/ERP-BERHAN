# erp/__init__.py
import importlib
import logging
import os
import pkgutil
from datetime import datetime

from flask import Flask, render_template
from flask_cors import CORS

from .extensions import (
    db, migrate, login_manager, mail, cache, limiter, socketio
)

def _register_blueprints(app: Flask) -> None:
    """Autodiscover and register all blueprints in erp.routes.* safely."""
    import erp.routes as routes_pkg  # noqa: F401

    package = routes_pkg
    package_prefix = package.__name__ + "."
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):  # type: ignore[attr-defined]
        module_fqn = f"{package_prefix}{module_name}"
        try:
            module = importlib.import_module(module_fqn)
        except Exception as e:  # don't crash app on a bad route module
            app.logger.error("Skipping routes module %s due to import error: %s", module_fqn, e)
            continue

        # Convention: each routes module exposes `<name>_bp` Blueprint
        bp_attr = [a for a in dir(module) if a.endswith("_bp")]
        for attr in bp_attr:
            bp = getattr(module, attr, None)
            try:
                if bp is not None:
                    app.register_blueprint(bp)
                    app.logger.info("Registered blueprint %s from %s", bp.name, module_fqn)
            except Exception as e:
                app.logger.error("Failed to register blueprint from %s: %s", module_fqn, e)


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # ---- Config ----
    cfg_path = os.getenv("FLASK_CONFIG", "erp.config.ProductionConfig")
    module_name, class_name = cfg_path.rsplit(".", 1)
    config_cls = getattr(importlib.import_module(module_name), class_name)
    app.config.from_object(config_cls)

    # Ensure DB URI is present (fixes: "Either SQLALCHEMY_DATABASE_URI or BINDS must be set")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        db_uri = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
        if not db_uri:
            raise RuntimeError("SQLALCHEMY_DATABASE_URI (or DATABASE_URL) is required")
        app.config["SQLALCHEMY_DATABASE_URI"] = db_uri

    # ---- Logging ----
    logging.basicConfig(level=logging.INFO)

    # ---- Extensions ----
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    CORS(app, resources={r"/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "main.choose_login"

    from erp.models import User  # local import to avoid circular refs

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return User.query.get(int(user_id))  # type: ignore[arg-type]
        except Exception:
            return None

    # SocketIO
    socketio.init_app(app, message_queue=None)

    # ---- Jinja context ----
    @app.context_processor
    def inject_branding():
        return dict(
            brand_name=app.config["BRAND_NAME"],
            brand_tagline=app.config["BRAND_TAGLINE"],
            brand_logo=app.config["BRAND_LOGO"],
            current_year=datetime.utcnow().year,
        )

    # ---- Error pages ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # ---- Routes ----
    _register_blueprints(app)

    return app


# re-export for wsgi
from .extensions import socketio  # noqa: E402
