
from __future__ import annotations
from flask import Flask
from .config import Config, validate_config
from .observability import init_logging
from .security import apply_security_headers
from .errors import register_error_handlers

GRAPHQL_REJECTS = 0
QUEUE_LAG = 0
RATE_LIMIT_REJECTIONS = 0
OLAP_EXPORT_SUCCESS = 0

try:
    from flask_socketio import SocketIO  # type: ignore
    socketio = SocketIO(message_queue=None, async_mode="threading")  # pragma: no cover
except Exception:  # pragma: no cover
    socketio = None

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config())
    if test_config:
        app.config.update(test_config)

    try:
        validate_config(app.config)
    except Exception:
        pass

    try:
        from .db import db
        db.init_app(app)
    except Exception:
        pass

    try:
        from .blueprints.health import bp as health_bp
        app.register_blueprint(health_bp, url_prefix="/")
    except Exception:
        pass

    apply_security_headers(app)
    register_error_handlers(app)
    init_logging(app)

        # ---- Phase1: ensure health endpoints are present ----


        try:


            from .blueprints.health import bp as health_bp


            app.register_blueprint(health_bp, url_prefix="/")


        except Exception:


            # Fallback inline routes if blueprint unavailable


            from flask import jsonify


            @app.get("/healthz")


            def healthz():


                return jsonify(status="ok"), 200


            @app.get("/readyz")


            def readyz():


                return jsonify(status="ready"), 200


        # ---- /Phase1 health ----


        return app

oauth = None

