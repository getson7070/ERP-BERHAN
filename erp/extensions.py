# erp/extensions.py
from __future__ import annotations

import os
from typing import Optional

from flask_babel import Babel
from flask_caching import Cache
from flask_cors import CORS
from flask_compress import Compress
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# ──────────────────────────────────────────────────────────────────────────────
# SQLAlchemy: define naming convention at construction time (immutable in SA 2.x)
# ──────────────────────────────────────────────────────────────────────────────
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
db = SQLAlchemy(metadata=MetaData(naming_convention=NAMING_CONVENTION))

# Other extensions
migrate = Migrate()
jwt = JWTManager()
cache = Cache()
cors = CORS()
compress = Compress()
babel = Babel()

# Flask-Limiter: pass storage_uri at construction (init_app() in v3.x takes no kw)
RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
limiter = Limiter(key_func=get_remote_address, storage_uri=RATELIMIT_STORAGE_URI)


def _coalesce_db_uri() -> Optional[str]:
    """
    Prefer SQLALCHEMY_DATABASE_URI, then DATABASE_URL (Render), then DATABASE_URI.
    Also normalize postgres:// → postgresql+psycopg2://
    """
    uri = (
        os.getenv("SQLALCHEMY_DATABASE_URI")
        or os.getenv("DATABASE_URL")
        or os.getenv("DATABASE_URI")
    )
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql+psycopg2://", 1)
    return uri


def init_extensions(app) -> None:
    # Database URI
    uri = _coalesce_db_uri()
    if uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Cache defaults (honor your existing envs)
    app.config.setdefault("CACHE_TYPE", os.getenv("CACHE_TYPE", "SimpleCache"))
    if "CACHE_DEFAULT_TIMEOUT" in os.environ:
        app.config["CACHE_DEFAULT_TIMEOUT"] = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))

    # CORS
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    app.config.setdefault("CORS_ORIGINS", cors_origins)

    # Init all
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": cors_origins}})
    compress.init_app(app)
    babel.init_app(app)
    limiter.init_app(app)
