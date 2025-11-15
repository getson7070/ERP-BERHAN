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
# erp/__init__.py
from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Iterable

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from erp.extensions import init_extensions  # must exist in erp/extensions.py


def _load_config(app: Flask) -> None:
    """
    Load configuration for the Flask app.

    Priority:
      1) erp.config.Config if present
      2) Fallback Config class that requires env vars:
         - SECRET_KEY
         - DATABASE_URL
    """
    try:
        from erp.config import Config  # type: ignore
    except ImportError:
        class Config:
            SECRET_KEY = os.environ["SECRET_KEY"]
            SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            WTF_CSRF_ENABLED = True

    app.config.from_object(Config)


# ---------- Blueprint discovery / registration ----------

def _iter_blueprint_modules() -> Iterable[str]:
    """
    Yield dotted module paths for blueprints listed in
    `blueprints_dedup_manifest.txt`.

    Lines starting with # or blank lines are ignored.
    """
    # erp/__init__.py -> erp/ -> project root
    root = Path(__file__).resolve().parent.parent
    manifest = root / "blueprints_dedup_manifest.txt"
    if not manifest.exists():
        return []

    modules: list[str] = []
    with manifest.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            modules.append(line)
    return modules


def _find_blueprint(module):
    """
    Return a Flask Blueprint object from a module.

    Preference:
      1. module.bp (common pattern)
      2. any attribute that looks like a Blueprint (has .name and .register)
    """
    from flask import Blueprint  # local import to avoid circular issues

    bp = getattr(module, "bp", None)
    if isinstance(bp, Blueprint):
        return bp

    for attr in module.__dict__.values():
        if isinstance(attr, Blueprint):
            return attr

    raise RuntimeError(f"No blueprint found in module {module.__name__!r}")


def register_blueprints(app: Flask) -> None:
    """
    Register all blueprints, skipping duplicates by (name, url_prefix).

    This prevents confusing errors when multiple modules reuse the same
    blueprint name or URL prefix. Duplicates are logged and skipped.
    """
    seen: dict[tuple[str, str], str] = {}

    for dotted_path in _iter_blueprint_modules():
        module = importlib.import_module(dotted_path)
        bp = _find_blueprint(module)

        name = bp.name
        prefix = bp.url_prefix or ""
        key = (name, prefix)

        if key in seen:
            app.logger.warning(
                "Skipping duplicate blueprint: name=%r prefix=%r from %s "
                "(already registered from %s)",
                name,
                prefix,
                dotted_path,
                seen[key],
            )
            continue

        app.register_blueprint(bp)
        seen[key] = dotted_path
        app.logger.info(
            "Registered blueprint %r (prefix=%r) from %s",
            name,
            prefix,
            dotted_path,
        )


# ---------- Core routes / utilities ----------

def _register_core_routes(app: Flask) -> None:
    """Register small core routes like /healthz."""

    @app.get("/healthz")
    def healthz():
        # Simple health check for Docker / LB probes
        return jsonify(status="ok")


# ---------- Application factory ----------

def create_app(config_object: str | None = None) -> Flask:
    """
    Flask application factory used by Gunicorn/Celery and `FLASK_APP=erp:create_app`.

    You can pass a dotted config path (e.g. "erp.config.DevConfig") in
    `config_object`, or rely on _load_config() defaults which read from env.
    """
    app = Flask(__name__, instance_relative_config=False)

    # ProxyFix so `request.url_root`, scheme, etc. are correct behind Nginx/Render
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    if config_object:
        app.config.from_object(config_object)
    else:
        _load_config(app)

    # Initialise db, migrate, login_manager, mail, cache, limiter, etc.
    init_extensions(app)

    # Register blueprints from manifest (with duplicate protection)
    register_blueprints(app)

    # Core routes such as /healthz
    _register_core_routes(app)

    return app

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
