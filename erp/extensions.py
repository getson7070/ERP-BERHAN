# erp/extensions.py
from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import MetaData

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Import SocketIO lazily inside init to avoid early eventlet/socket decisions

# -----------------------------------------------------------------------------
# SQLAlchemy with fixed naming convention (set at construction, no runtime update)
# -----------------------------------------------------------------------------
_naming = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
db = SQLAlchemy(metadata=MetaData(naming_convention=_naming))
migrate = Migrate()

# -----------------------------------------------------------------------------
# Other extensions (constructed without app, configured later)
# -----------------------------------------------------------------------------
cache = Cache()
cors = CORS()

# Build Limiter in init_extensions (v3+ requires storage_uri at construction)
_limiter: Optional[Limiter] = None

# JWTManager must be imported only inside init_extensions
_jwt = None  # will hold the JWTManager instance

_socketio = None  # will hold SocketIO instance


def init_extensions(app: Flask):
    """
    Initialize extensions after Eventlet monkey_patch() has already executed
    (done in wsgi.py). No JWT imports at module import time.
    """
    global _limiter, _jwt, _socketio

    # ---- Basic Flask config fallbacks ----
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Database URL must be present
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        # Try standard env vars as a fallback
        db_url = (
            os.getenv("SQLALCHEMY_DATABASE_URI")
            or os.getenv("DATABASE_URL")
            or os.getenv("POSTGRES_URL")
        )
        if db_url:
            app.config["SQLALCHEMY_DATABASE_URI"] = db_url

    # ---- Init core extensions ----
    db.init_app(app)
    migrate.init_app(app, db)

    # Cache (optional)
    cache_type = app.config.get("CACHE_TYPE")  # None/NullCache by default on Render
    cache.init_app(app, config={"CACHE_TYPE": cache_type} if cache_type else {})

    # CORS
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    # ---- Limiter (Flask-Limiter v3+) ----
    storage_uri = (
        app.config.get("RATELIMIT_STORAGE_URI")
        or os.getenv("RATELIMIT_STORAGE_URI")
        or os.getenv("REDIS_URL")  # often used on Render
        or "memory://"
    )
    # Build Limiter with storage_uri at construction time (no storage_uri in init_app)
    _limiter = Limiter(
        key_func=get_remote_address,
        default_limits=app.config.get("DEFAULT_RATE_LIMITS", []),
        storage_uri=storage_uri,
        strategy=app.config.get("RATELIMIT_STRATEGY", "fixed-window"),
        headers_enabled=True,
    )
    _limiter.init_app(app)

    # ---- JWT (defer import to here to avoid early LocalProxy creation) ----
    from flask_jwt_extended import JWTManager  # noqa: WPS433

    _jwt = JWTManager()
    _jwt.init_app(app)

    # Optional: custom JWT claims loader examples (safe, no ctx usage here)
    @_jwt.additional_claims_loader
    def _add_claims(identity):
        # Return a dict of claims; keep lightweight
        return {"roles": getattr(identity, "roles", []) if identity else []}

    # ---- Socket.IO (optional; defer import so eventlet is already patched) ----
    if app.config.get("ENABLE_SOCKETIO") or os.getenv("ENABLE_SOCKETIO"):
        from flask_socketio import SocketIO  # noqa: WPS433

        _socketio = SocketIO(  # type: ignore[call-arg]
            async_mode="eventlet",
            message_queue=os.getenv("REDIS_URL"),  # optional
            cors_allowed_origins="*",
            logger=app.logger,
            engineio_logger=False,
        )
        _socketio.init_app(app)

    # Expose commonly used objects on app for convenience (optional)
    app.extensions["db"] = db
    app.extensions["migrate"] = migrate
    app.extensions["cache"] = cache
    app.extensions["cors"] = cors
    app.extensions["limiter"] = _limiter
    app.extensions["jwt"] = _jwt
    if _socketio:
        app.extensions["socketio"] = _socketio


# Small helpers to access optional singletons if you need them elsewhere
def get_limiter() -> Optional[Limiter]:
    return _limiter


def get_jwt_manager():
    return _jwt


def get_socketio():
    return _socketio
