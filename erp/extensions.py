# erp/extensions.py
from __future__ import annotations

from typing import Optional, Dict
from sqlalchemy import MetaData
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
from flask_jwt_extended import JWTManager

# --- SQLAlchemy with naming convention set at creation time (avoids immutabledict error)
NAMING_CONVENTION: Dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
db = SQLAlchemy(metadata=MetaData(naming_convention=NAMING_CONVENTION))
migrate = Migrate()

oauth = OAuth()
# Limiter v3+: configure storage URI at init_app
limiter = Limiter(key_func=get_remote_address)
cors = CORS()
cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()
jwt = JWTManager()

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)

    # Rate limiting storage (defaults to in-memory)
    storage_uri = app.config.get("RATELIMIT_STORAGE_URI", "memory://")
    limiter.init_app(app, storage_uri=storage_uri, default_limits=app.config.get("DEFAULT_RATE_LIMITS", []))

    cors.init_app(app, resources=app.config.get("CORS_RESOURCES", {r"*": {"origins": "*"}}))
    cache.init_app(app, config=app.config.get("CACHE", {"CACHE_TYPE": "NullCache"}))
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)
    jwt.init_app(app)
    oauth.init_app(app)

__all__ = [
    "db", "migrate", "oauth", "limiter", "cors", "cache", "compress", "csrf", "babel", "jwt",
    "init_extensions",
]
