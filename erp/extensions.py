# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()

# Redis is optional per requirement; default to in-memory.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=None,  # in-memory; set to "redis://..." when you enable Redis
    default_limits=["200 per hour"],  # adjust as needed
)
