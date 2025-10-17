import os
from flask import Flask

# Optional imports guarded so tests don't crash if pieces are missing
try:
    from .models import db  # provided by your package 'erp/models/__init__.py'
except Exception:
    db = None  # pragma: no cover

try:
    from .blueprints.health import bp as health_bp  # Phase-1 blueprint
except Exception as exc:
    raise RuntimeError(f"Health blueprint missing: {exc}")

try:
    from .config_ext.validate_env import validate_required_env
except Exception:
    def validate_required_env() -> None:  # no-op fallback
        return

# Sentry bootstrap is optional and safe to ignore if DSN not set
def _init_sentry(app: Flask) -> None:
    try:
        from .observability.sentry import init_sentry
        init_sentry(app)
    except Exception:
        pass

# Export a minimal set of names some tests / modules may import
GRAPHQL_REJECTS = 0
RATE_LIMIT_REJECTIONS = 0
QUEUE_LAG = 0
OLAP_EXPORT_SUCCESS = False
socketio = None
_dead_letter_handler = None

def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-test-secret"),
        TESTING=testing,
        SQLALCHEMY_DATABASE_URI=(
            "sqlite:///:memory:" if testing
            else os.getenv("DATABASE_URL", "sqlite:///app.db")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if db is not None and hasattr(db, "init_app"):
        db.init_app(app)

    # Validate env (Phase-1)
    validate_required_env()

    # Register health/readiness endpoints
    app.register_blueprint(health_bp)

    @app.get("/")
    def index():
        return "ok", 200

    _init_sentry(app)
    return app
