from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})  # OK for now
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
