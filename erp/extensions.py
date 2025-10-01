# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()
limiter = Limiter(key_func=get_remote_address)  # v3+ pattern
cors = CORS()

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)
    limiter.init_app(app)
    cors.init_app(app)
