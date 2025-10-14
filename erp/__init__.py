
from __future__ import annotations
import os, pkgutil, importlib, traceback
from typing import List, Tuple
from flask import Flask, Blueprint
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

# Extensions
from .extensions import db, migrate, login_manager, limiter, socketio

_IMPORT_FAILURES: List[Tuple[str, str]] = []  # (module, error)

csrf = CSRFProtect()

def _init_extensions(app: Flask) -> None:
    # Init core extensions
    for ext in (db, migrate, login_manager, limiter):
        if hasattr(ext, "init_app"):
            ext.init_app(app)
    if hasattr(socketio, "init_app"):
        socketio.init_app(app, async_mode="eventlet", cors_allowed_origins="*", logger=False, engineio_logger=False)

    # CSRF
    csrf.init_app(app)
    # Expose csrf_token() to Jinja
    @app.context_processor
    def inject_csrf():
        return dict(csrf_token=generate_csrf)

    # Flask-Login sane defaults
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"

def _try_import(name: str):
    try:
        return importlib.import_module(name), None
    except Exception as e:
        _IMPORT_FAILURES.append((name, f"{e}\n" + traceback.format_exc()))
        return None, e

def _register_blueprints_autodiscover(app: Flask) -> None:
    visited = set()
    packages = [
        "erp.routes",
        "erp.inventory", "erp.finance", "erp.procurement", "erp.sales", "erp.hr", "erp.crm"
    ]
    for pkg_name in packages:
        pkg, err = _try_import(pkg_name)
        if err:
            continue
        prefix = pkg.__name__ + "."
        for _, modname, ispkg in pkgutil.walk_packages(pkg.__path__, prefix):
            if ispkg:
                continue
            mod, e2 = _try_import(modname)
            if e2:
                continue
            for obj_name in dir(mod):
                obj = getattr(mod, obj_name)
                if isinstance(obj, Blueprint):
                    try:
                        app.register_blueprint(obj)
                        visited.add(obj.name)
                    except Exception as e:
                        _IMPORT_FAILURES.append((modname + ":" + obj_name, f"{e}\n" + traceback.format_exc()))
    app.config["IMPORT_FAILURES"] = _IMPORT_FAILURES
    app.config["REGISTERED_BLUEPRINTS"] = sorted(list(visited))

def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    # Config
    if config_object:
        app.config.from_object(config_object)
    else:
        # Default to Production config unless FLASK_ENV=development
        from .config import ProductionConfig, DevelopmentConfig
        env = os.getenv("FLASK_ENV", "production").lower()
        app.config.from_object(DevelopmentConfig if env.startswith("dev") else ProductionConfig)

    # Ensure a secret key exists (required for sessions & CSRF)
    sk = app.config.get("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY")
    if not sk:
        # Hard fail with clear message instead of silent 500s
        raise RuntimeError("SECRET_KEY is not set. Set FLASK_SECRET_KEY or SECRET_KEY in environment/config.")
    app.secret_key = sk

    # Security cookie hardening
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SECURE", os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true")

    _init_extensions(app)
    _register_blueprints_autodiscover(app)

    @app.get("/healthz")
    def _healthz():
        return {"status": "ok", "blueprints": app.config.get("REGISTERED_BLUEPRINTS", []), "import_failures": len(_IMPORT_FAILURES)}, 200

    return app
