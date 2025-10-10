# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager, AnonymousUserMixin

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()

# Anonymous user with a default role
class Anonymous(AnonymousUserMixin):
    role = "anonymous"

login_manager.anonymous_user = Anonymous
