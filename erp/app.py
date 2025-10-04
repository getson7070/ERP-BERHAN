# erp/app.py  (full replacement)
import os
from flask import Flask, jsonify
from .extensions import socketio


def _choose_async_mode() -> str:
    """
    Pick a safe async mode. If an invalid env value is provided, ignore it.
    Prefer eventlet when available; otherwise fallback to threading so the app still boots.
    """
    raw = os.getenv("SOCKETIO_ASYNC_MODE") or os.getenv("ASYNC_MODE")
    allowed = {None, "eventlet", "gevent", "threading"}
    if raw not in allowed:
        raw = None

    if raw in (None, "eventlet"):
        try:
            import eventlet  # noqa: F401
            return "eventlet"
        except Exception:
            return "threading"
    return raw  # "gevent" or "threading"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    @app.get("/")
    def health():
        return jsonify({"app": "ERP-BERHAN", "status": "running"})

    register_extensions(app)
    register_blueprints(app)
    return app


def register_extensions(app: Flask) -> None:
    async_mode = _choose_async_mode()
    socketio.init_app(app, async_mode=async_mode, cors_allowed_origins="*")
    try:
        app.logger.info(f"Flask-SocketIO async_mode: {async_mode}")
    except Exception:
        pass


def register_blueprints(app: Flask) -> None:
    # Register your blueprints here.
    # Example:
    # from .api import api_bp
    # app.register_blueprint(api_bp, url_prefix="/api")
    return
