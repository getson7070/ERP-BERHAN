from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
from flask_login import LoginManager
try:
    from .db import db  # reuse shared instance
except Exception:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.session_protection = "strong"

@login_manager.user_loader
def _load_user(user_id: str):
    try:
        from .models import User
        return User.query.get(int(user_id))
    except Exception:
        return None
