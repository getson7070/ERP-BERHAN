import os
from importlib import import_module

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# ---- global extensions ----
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def _load_config(app: Flask) -> None:
    """
    Load configuration for the app.

    Priority:
    1. erp.config.Config if present
    2. Fallback minimal settings (Docker dev)
    """
    try:
        from .config import Config  # type: ignore
    except ImportError:
        Config = None  # type: ignore

    if Config is not None:
        app.config.from_object(Config)
    else:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-CHANGE-ME"),
            SQLALCHEMY_DATABASE_URI=(
                os.environ.get("DATABASE_URL")
                or "postgresql+psycopg://erp:erp@db:5432/erp"
            ),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )


def _find_blueprint(module_name: str, *candidate_attrs: str):
    """
    Try a few common locations/attribute names to find a Blueprint.

    Example:
        _find_blueprint("erp.auth", "bp", "auth_bp")
        _find_blueprint("erp.main", "bp", "main_bp")
    """
    last_err = None

    # 1) module itself: erp.auth
    try:
        mod = import_module(module_name)
        for name in candidate_attrs:
            bp = getattr(mod, name, None)
            if bp is not None:
                return bp
    except ImportError as e:
        last_err = e

    # 2) routes submodule: erp.auth.routes
    try:
        routes_mod = import_module(f"{module_name}.routes")
        for name in candidate_attrs:
            bp = getattr(routes_mod, name, None)
            if bp is not None:
                return bp
    except ImportError as e:
        last_err = e

    msg = f"Could not find blueprint in {module_name} (tried attrs: {candidate_attrs})"
    if last_err is not None:
        msg += f" – last import error: {last_err}"
    raise RuntimeError(msg)


def create_app() -> Flask:
    """
    Application factory used by:
    - FLASK_APP=erp:create_app
    - Alembic migrations/env.py
    - docker/entrypoint.sh via wsgi.py
    """
    app = Flask(__name__)

    # config
    _load_config(app)

    # extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # models (for Alembic)
    from . import models  # noqa: F401

    # blueprints (be tolerant to different names)
    try:
        auth_bp = _find_blueprint("erp.auth", "bp", "auth_bp", "auth")
        app.register_blueprint(auth_bp, url_prefix="/auth")
    except Exception as e:
        # Fail fast with a clear message if auth BP truly missing
        raise RuntimeError(f"Failed to register auth blueprint: {e}") from e

    try:
        main_bp = _find_blueprint("erp.main", "bp", "main_bp", "main")
        app.register_blueprint(main_bp)
    except Exception as e:
        raise RuntimeError(f"Failed to register main blueprint: {e}") from e

    # health check
    @app.get("/healthz")
    def healthz():
        return "ok", 200

    return app
