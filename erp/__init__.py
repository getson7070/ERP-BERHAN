
from __future__ import annotations
import os, pkgutil, importlib, traceback
from typing import List, Tuple
from flask import Flask, Blueprint
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from .extensions import db, migrate, login_manager, limiter, socketio

csrf = CSRFProtect()
_IMPORT_FAILURES: List[Tuple[str,str]] = []

def _init_extensions(app: Flask) -> None:
    for ext in (db, migrate, login_manager, limiter):
        if hasattr(ext, "init_app"):
            ext.init_app(app)
    socketio.init_app(app, async_mode="eventlet", cors_allowed_origins="*")
    csrf.init_app(app)
    @app.context_processor
    def _inject_csrf():
        return dict(csrf_token=generate_csrf)
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"

def _try_import(name: str):
    try:
        return importlib.import_module(name), None
    except Exception as e:
        _IMPORT_FAILURES.append((name, f"{e}\n{traceback.format_exc()}"))
        return None, e

def _register_blueprints(app: Flask) -> None:
    visited = set()
    for base in ["erp.routes","erp.inventory","erp.finance","erp.procurement","erp.sales","erp.hr","erp.crm"]:
        mod, err = _try_import(base)
        if err: continue
        for _, sub, ispkg in pkgutil.walk_packages(mod.__path__, mod.__name__ + "."):
            if ispkg: continue
            m, e2 = _try_import(sub); 
            if e2: continue
            for name in dir(m):
                obj = getattr(m, name)
                if isinstance(obj, Blueprint):
                    try:
                        app.register_blueprint(obj)
                        visited.add(obj.name)
                    except Exception as e:
                        _IMPORT_FAILURES.append((sub + ":" + name, f"{e}\n{traceback.format_exc()}"))
    app.config["REGISTERED_BLUEPRINTS"] = sorted(list(visited))
    app.config["IMPORT_FAILURES"] = _IMPORT_FAILURES

def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    if config_object:
        app.config.from_object(config_object)
    else:
        from .config import ProductionConfig, DevelopmentConfig
        env = os.getenv("FLASK_ENV", "production").lower()
        app.config.from_object(DevelopmentConfig if env.startswith("dev") else ProductionConfig)

    secret = app.config.get("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY missing. Set FLASK_SECRET_KEY or config.SECRET_KEY.")
    app.secret_key = secret

    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SECURE", os.getenv("SESSION_COOKIE_SECURE","true").lower()=="true")

    _init_extensions(app)
    _register_blueprints(app)

    @app.get("/healthz")
    def healthz():
        return {"ok": True, "blueprints": app.config["REGISTERED_BLUEPRINTS"], "import_failures": app.config["IMPORT_FAILURES"]}, 200
    return app
