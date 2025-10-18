from flask import Flask

# --- test-visible counters (simple stubs) ---
GRAPHQL_REJECTS = 0
QUEUE_LAG = 0
RATE_LIMIT_REJECTIONS = 0
OLAP_EXPORT_SUCCESS = 0

def _dead_letter_handler(*args, **kwargs):
    return None

try:
    from flask_socketio import SocketIO          # optional in Phase-1
    socketio = SocketIO(message_queue=None, async_mode="threading")
except Exception:
    socketio = None

def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = app.config.get("SECRET_KEY") or "test-secret"

    # Initialize db if present
    try:
        from .db import db
        db.init_app(app)
    except Exception:
        pass

    # Health/readiness endpoints from Phase-1
    from .blueprints.health import bp as health_bp
    app.register_blueprint(health_bp, url_prefix="/")

    return app


oauth = None
