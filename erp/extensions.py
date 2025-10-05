# erp/extensions.py
from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
login_manager = LoginManager()
cors = CORS()
