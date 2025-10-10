# erp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # adjust if different

@login_manager.user_loader
def load_user(user_id):
    """Return user or None; prevents Flask-Login from crashing templates when unauthenticated."""
    try:
        from erp.models import User  # avoid circular import on module import
        return User.query.get(int(user_id))
    except Exception:
        return None
