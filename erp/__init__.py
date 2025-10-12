import os
import pkgutil
import importlib

from flask import Flask, render_template, Blueprint
from flask_migrate import Migrate
from .extensions import db, login_manager
from .config import DevelopmentConfig, ProductionConfig


def _register_blueprints(app: Flask) -> None:
    """Import and register every Blueprint under erp.routes.*"""
    import erp.routes as routes_pkg

    for _finder, module_name, _ispkg in pkgutil.iter_modules(routes_pkg.__path__):
        module = importlib.import_module(f"{routes_pkg.__name__}.{module_name}")
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, Blueprint):
                app.register_blueprint(obj)


def create_app() -> Flask:
    # Keep templates/static inside the erp package
    app = Flask(__name__, template_folder="templates", static_folder="static")

    env = os.getenv("APP_ENV", "production")
    if env == "development":
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(ProductionConfig)

    # --- Extensions ---
    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Import models so Flask-Login/SQLAlchemy can see them
    from .models import User  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # --- Blueprints ---
    _register_blueprints(app)

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):  # pragma: no cover
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):  # pragma: no cover
        return render_template("errors/500.html"), 500

    # Fallback health endpoint (routes.health provides /health once registered)
    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app
