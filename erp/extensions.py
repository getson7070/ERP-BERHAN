# erp/extensions.py
from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

try:
    # Optional: only present in some envs
    from flask_limiter import Limiter  # type: ignore
    from flask_limiter.util import get_remote_address  # type: ignore
except Exception:
    Limiter = None
    get_remote_address = None  # type: ignore

db = SQLAlchemy()
migrate = Migrate()

class _NoopLimiter:
    """Fallback when flask-limiter isn't installed/configured."""
    def init_app(self, app):
        app.logger.info("Limiter disabled (noop).")

# Export a limiter object that always exists.
limiter = _NoopLimiter() if Limiter is None else Limiter(key_func=get_remote_address)

def init_extensions(app):
    """Centralized extension initialization."""
    db.init_app(app)
    migrate.init_app(app, db)
    try:
        limiter.init_app(app)
    except Exception as e:
        # Don't block the app for optional limiter issues
        app.logger.warning("Limiter not initialized: %s", e)
