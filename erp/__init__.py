from __future__ import annotations

# --- Minimal Flask import (safe at import time) ---
try:
    from flask import Flask
except Exception:
    # Lightweight shim so importing `erp` in limited envs doesn't explode
    class Flask:  # type: ignore
        def __init__(self, *a, **kw): ...
        def register_blueprint(self, *a, **kw): ...

# --- SocketIO: safe fallback with no-op init_app ---
try:
    from flask_socketio import SocketIO  # type: ignore
except Exception:
    class SocketIO:  # type: ignore
        def __init__(self, *a, **kw): ...
        def init_app(self, app): ...
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)

    # Register blueprints defensively (don’t break imports if missing)
    try:
        from erp.ops.status import bp as status_bp
        app.register_blueprint(status_bp)
    except Exception:
        pass

    try:
        from erp.auth.mfa_routes import bp as mfa_bp
        app.register_blueprint(mfa_bp)
    except Exception:
        pass

    try:
        socketio.init_app(app)
    except Exception:
        pass

    return app

# Re-export test contracts from metrics (constants + handler)
from erp.metrics import (
    QUEUE_LAG,
    RATE_LIMIT_REJECTIONS,
    GRAPHQL_REJECTS,
    AUDIT_CHAIN_BROKEN,
    OLAP_EXPORT_SUCCESS,
    _dead_letter_handler,
)

__all__ = [
    "create_app",
    "socketio",
    "QUEUE_LAG",
    "RATE_LIMIT_REJECTIONS",
    "GRAPHQL_REJECTS",
    "AUDIT_CHAIN_BROKEN",
    "OLAP_EXPORT_SUCCESS",
    "_dead_letter_handler",
]
