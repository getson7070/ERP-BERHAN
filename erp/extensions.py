# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_caching import Cache
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cors = CORS()
cache = Cache()
mail = Mail()

# For Flask-Limiter 3.x, create Limiter with key_func; configure storage via app.config
limiter = Limiter(key_func=get_remote_address)
