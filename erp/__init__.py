from __future__ import annotations
from erp.ops.status import bp as status_bp
from erp.ops.doctor import bp as doctor_bp
from erp.auth.mfa_routes import bp as mfa_bp

import importlib, pkgutil, os
from flask import Flask, Response
from .extensions import csrf, limiter, login_manager, db

try:
    from db import redis_client  # back-compat: "from erp import redis_client"
except Exception:
    redis_client = None  # type: ignore

def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def _h(resp: Response) -> Response:
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        resp.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'")
        return resp

def _autodiscover_and_register_blueprints(app: Flask) -> None:
    try:
        import erp.routes as routes_pkg  # type: ignore
        for m in [m.name for m in pkgutil.iter_modules(routes_pkg.__path__)]:
            try:
                mod = importlib.import_module(f"erp.routes.{m}")
                bp = getattr(mod, "bp", None)
                if bp is not None:
                    app.register_blueprint(bp)
            except Exception:
                continue
    except Exception:
        pass

def create_app(config: dict | None = None) -> Flask:
    app = Flask("erp")
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret"))
    app.config.setdefault("JSONIFY_PRETTYPRINT_REGULAR", False)
    csrf.init_app(app)
    limiter.init_app(app)
    try:
        login_manager.init_app(app)  # type: ignore[attr-defined]
    except Exception:
        pass
    _autodiscover_and_register_blueprints(app)
    _register_security_headers(app)

    @app.get("/healthz")
    def _healthz():
        return {"ok": True}
    app.register_blueprint(status_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(mfa_bp)
    return app

__all__ = [,'QUEUE_LAG','RATE_LIMIT_REJECTIONS','GRAPHQL_REJECTS','AUDIT_CHAIN_BROKEN','OLAP_EXPORT_SUCCESS','_dead_letter_handler']


# --- [autogen] SocketIO export invariant (idempotent) ---
try:
    from flask_socketio import SocketIO  # type: ignore
    if "socketio" not in globals():
        _app_for_socket = None
        try:
            if "create_app" in globals():
                _app_for_socket = create_app(testing=True) if "testing" in create_app.__code__.co_varnames else create_app()
        except Exception:
            _app_for_socket = None
        socketio = SocketIO(_app_for_socket, cors_allowed_origins="*")  # noqa: F401
        try:
            __all__  # noqa
        except NameError:
            __all__ = [,'QUEUE_LAG','RATE_LIMIT_REJECTIONS','GRAPHQL_REJECTS','AUDIT_CHAIN_BROKEN','OLAP_EXPORT_SUCCESS','_dead_letter_handler']
        if "socketio" not in __all__:
            __all__.append("socketio")
except Exception as _e:
    pass
# --- [/autogen] ---





