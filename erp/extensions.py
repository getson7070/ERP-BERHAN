# erp/extensions.py
from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager

# Database + migrations
db = SQLAlchemy()
migrate = Migrate()

# Caching (configured in app via CACHE_TYPE / CACHE_DEFAULT_TIMEOUT)
cache = Cache()

# Rate limiter (storage & default limits configured in app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],           # we’ll set from env in create_app()
    storage_uri=None,            # we’ll set from env in create_app()
)

# Login manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.session_protection = "strong"
