from __future__ import annotations
import os
import pkgutil
import importlib
from flask import Flask, Blueprint
from werkzeug.middleware.proxy_fix import ProxyFix

# Expecting these in your project; adjust if differing
try:
    from erp.extensions import db, migrate, login_manager, limiter, socketio  # type: ignore
except Exception:  # fallback names for older codebases
    db = migrate = login_manager = limiter = socketio = None  # type: ignore

def _init_extensions(app: Flask) -> None:
    # Initialize extensions safely if present
    for ext in (db, migrate, login_manager, limiter):
        if hasattr(ext, "init_app"):
            ext.init_app(app)
    # SocketIO optional (gunicorn/eventlet)
    if hasattr(socketio, "init_app"):
        socketio.init_app(app, async_mode="eventlet", cors_allowed_origins="*", logger=False, engineio_logger=False)

def _register_blueprints_autodiscover(app: Flask) -> None:
    """Discover and register all Flask Blueprints under known ERP packages."""
    visited = set()
    def _register_bp(obj):
        if isinstance(obj, Blueprint):
            if obj.name not in visited:
                app.register_blueprint(obj)
                visited.add(obj.name)

    packages = [
        "erp.routes",
        "erp.inventory", "erp.finance", "erp.procurement", "erp.sales", "erp.hr", "erp.crm",
        "erp.analytics", "erp.admin", "erp.reports", "erp.plugins", "erp.tenders", "erp.manufacturing",
        "erp.api", "erp.dashboard_customize",
    ]
    for pkg_name in packages:
        try:
            pkg = importlib.import_module(pkg_name)
        except Exception:
            continue
        # Register any blueprint directly on the package (rare)
        for v in vars(pkg).values():
            _register_bp(v)
        # Walk submodules
        pkg_path = getattr(pkg, "__path__", None)
        if not pkg_path:
            continue
        for finder, name, ispkg in pkgutil.walk_packages(pkg_path, pkg.__name__ + "."):
            try:
                mod = importlib.import_module(name)
            except Exception:
                continue
            for v in vars(mod).values():
                _register_bp(v)

def create_app(config_object: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    # Load configuration
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret-key"))
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.environ.get("DATABASE_URL", "sqlite:///app.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)  # behind proxy

    # external config module path support
    if config_object:
        app.config.from_object(config_object)

    _init_extensions(app)
    _register_blueprints_autodiscover(app)

    # Basic health route if not provided
    @app.get("/healthz")
    def _healthz():
        return {"status": "ok"}, 200

    return app
