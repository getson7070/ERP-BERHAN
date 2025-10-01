# erp/extensions.py
from __future__ import annotations

import os
from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_caching import Cache
from flask_compress import Compress
from flask_wtf import CSRFProtect
from flask_babel import Babel
from flask_socketio import SocketIO

# IMPORTANT:
# Do NOT import from flask_jwt_extended at module import time.
# Lazily import JWTManager inside init_extensions() AFTER Eventlet greening.

# Core extensions
db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()
limiter = Limiter(key_func=get_remote_address)  # storage configured via app.config
cors = CORS()

# Optional extras
cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()

# JWT created lazily
jwt = None  # type: ignore[assignment]

# Realtime (eventlet backend)
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")


def _coerce_db_url(url: Optional[str]) -> Optional[str]:
    """
    Normalize DB URLs:
      - postgres:// -> postgresql+psycopg2://
      - ensure sslmode=require if missing
    """
    if not url:
        return None
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    scheme = url.split("://", 1)[0]
    if scheme == "postgresql" and "+psycopg2" not in scheme:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def init_extensions(app):
    """
    Initialize all Flask extensions with the Flask app.
    Call this from erp.app:create_app().
    """
    # ----------------------------
    # Database & migrations
    # ----------------------------
    raw_url = app.config.get("SQLALCHEMY_DATABASE_URI") or os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    final_url = _coerce_db_url(raw_url)
    if not final_url:
        raise RuntimeError("Either 'SQLALCHEMY_DATABASE_URI' or 'DATABASE_URL' must be set.")
    app.config["SQLALCHEMY_DATABASE_URI"] = final_url
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)
    migrate.init_app(app, db)

    # ----------------------------
    # OAuth
    # ----------------------------
    oauth.init_app(app)

    # ----------------------------
    # CORS
    # ----------------------------
    origins = app.config.get("CORS_ORIGINS", "*")
    if isinstance(origins, str) and origins != "*":
        origins = [o.strip() for o in origins.split(",") if o.strip()]
    cors.init_app(app, resources={r"/*": {"origins": origins}})

    # ----------------------------
    # Rate Limiter (Flask-Limiter 3.x)
    # ----------------------------
    storage_uri = app.config.get("RATELIMIT_STORAGE_URI") or os.getenv("RATELIMIT_STORAGE_URI")
    if not storage_uri:
        # To use Redis in prod: RATELIMIT_STORAGE_URI=redis://:password@host:6379/0
        storage_uri = "memory://"
    app.config["RATELIMIT_STORAGE_URI"] = storage_uri
    app.config.setdefault("RATELIMIT_DEFAULT", "60 per minute")
    limiter.init_app(app)

    # ----------------------------
    # Cache / Compression / CSRF / i18n
    # ----------------------------
    app.config.setdefault("CACHE_TYPE", "SimpleCache")
    app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 300)
    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)

    # ----------------------------
    # JWT (lazy import AFTER greening)
    # ----------------------------
    global jwt
    from flask_jwt_extended import JWTManager  # noqa: WPS433

    jwt = JWTManager()
    app.config.setdefault("JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "change-me-please"))
    jwt.init_app(app)

    # ----------------------------
    # Socket.IO (optional Redis message queue)
    # ----------------------------
    socketio.init_app(app, message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"))


__all__ = [
    "db",
    "migrate",
    "oauth",
    "limiter",
    "cors",
    "cache",
    "compress",
    "csrf",
    "babel",
    "jwt",
    "socketio",
    "init_extensions",
]
