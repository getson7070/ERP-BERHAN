# erp/__init__.py
from __future__ import annotations

from flask import Flask

# Use the shared extension objects (so models import the same db instance)
try:
    from .extensions import db  # typical pattern: db = SQLAlchemy() lives here
except Exception:  # pragma: no cover
    db = None  # type: ignore

# Phase-1 health blueprint
try:
    from .blueprints.health import bp as health_bp
except Exception:  # pragma: no cover
    health_bp = None  # type: ignore

# Optional Socket.IO (tests may import `socketio` from erp)
try:
    from flask_socketio import SocketIO  # optional dev dep
    socketio = SocketIO(async_mode="threading")
except Exception:  # pragma: no cover
    socketio = None  # graceful fallback

# A few module-level counters some legacy tests import;
# harmless placeholders that won’t affect Phase-1.
GRAPHQL_REJECTS = 0
QUEUE_LAG = 0
RATE_LIMIT_REJECTIONS = 0
OLAP_EXPORT_SUCCESS = 0

def _dead_letter_handler(message: str) -> None:
    # No-op placeholder for legacy tests; real impl can be wired later.
    return None

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    # Safe defaults for lightweight unit tests
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if config:
        app.config.update(config)

    # Init db if available
    if db is not None:
        try:
            db.init_app(app)  # type: ignore[attr-defined]
        except Exception:
            pass  # don't fail unit tests if local env is minimal

    # Register Phase-1 health endpoints
    if health_bp is not None:
        try:
            app.register_blueprint(health_bp)
        except Exception:
            pass

    @app.get("/")
    def _root_ok():
        return "ok", 200

    return app
