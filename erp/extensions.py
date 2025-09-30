# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_compress import Compress
from flask_wtf import CSRFProtect
from flask_babel import Babel

# Centralized singletons so routes can do: from erp import limiter, oauth, db, ...
db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address)  # storage configured via app.config
oauth = OAuth()
jwt = JWTManager()
cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()
