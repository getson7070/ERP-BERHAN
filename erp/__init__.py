from __future__ import annotations
import os, pkgutil, importlib, traceback
from typing import List, Tuple
from flask import Flask, Blueprint, current_app

# Expected extensions; missing ones are tolerated
try:
    from erp.extensions import db, migrate, login_manager, limiter, socketio  # type: ignore
except Exception:
    db = migrate = login_manager = limiter = socketio = None  # type: ignore

_IMPORT_FAILURES: List[Tuple[str, str]] = []  # (module, error)

def _init_extensions(app: Flask) -> None:
    for ext in (db, migrate, login_manager, limiter):
        if hasattr(ext, "init_app"):
            ext.init_app(app)
    if hasattr(socketio, "init_app"):
        socketio.init_app(app, async_mode="eventlet", cors_allowed_origins="*", logger=False, engineio_logger=False)

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
        "erp.inventory", "erp.finance", "erp.procurement", "erp.sales", "erp.hr", "erp.crm",
        "erp.analytics", "erp.admin", "erp.reports", "erp.plugins", "erp.tenders", "erp.manufacturing",
        "erp.api", "erp.dashboard_customize", "erp.observability",
        "erp.auth"]
    strict = os.getenv("STRICT_BP_IMPORTS", "0") == "1"

    def _register_bp(obj):
        if isinstance(obj, Blueprint) and obj.name not in visited:
            app.register_blueprint(obj)
            visited.add(obj.name)

    for pkg_name in packages:
        pkg, err = _try_import(pkg_name)
        if err and strict:
            raise err
        if not pkg:
            continue
        # direct blueprints on package
        for v in vars(pkg).values():
            _register_bp(v)
        # walk submodules
        pkg_path = getattr(pkg, "__path__", None)
        if not pkg_path:
            continue
        for _, name, _ in pkgutil.walk_packages(pkg_path, pkg.__name__ + "."):
            mod, err = _try_import(name)
            if err and strict:
                raise err
            if not mod:
                continue
            for v in vars(mod).values():
                _register_bp(v)

    # Store diagnostics for admin UI
    app.config["IMPORT_FAILURES"] = _IMPORT_FAILURES
    app.config["REGISTERED_BLUEPRINTS"] = sorted(list(visited))

def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret-key"))
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.environ.get("DATABASE_URL", "sqlite:///app.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    if config_object:
        app.config.from_object(config_object)

    _init_extensions(app)
    _register_blueprints_autodiscover(app)

    # Mount diagnostics if present
    try:
        from erp.observability.diagnostics import diagnostics_bp  # type: ignore
        app.register_blueprint(diagnostics_bp, url_prefix="/admin")
    except Exception:
        pass

    @app.get("/healthz")
    def _healthz():
        return {"status": "ok", "blueprints": app.config.get("REGISTERED_BLUEPRINTS", [])}, 200

    return app
