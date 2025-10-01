# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# New imports to satisfy erp/app.py
from flask_caching import Cache
from flask_compress import Compress
from flask_wtf import CSRFProtect
from flask_babel import Babel
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()
limiter = Limiter(key_func=get_remote_address)  # default limits can be set in config
cors = CORS()

# Added instances expected by erp/app.py
cache = Cache()
compress = Compress()
csrf = CSRFProtect()
babel = Babel()
jwt = JWTManager()
# SocketIO is initialized with eventlet async mode to match your Gunicorn worker
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)
    limiter.init_app(app)
    cors.init_app(app)

    cache.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    babel.init_app(app)
    jwt.init_app(app)
    # IMPORTANT: erp/app.py also calls socketio.init_app(app). This is harmless double-init.
    # If you prefer, remove that call in erp/app.py after you verify this works.
