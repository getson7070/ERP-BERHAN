# erp/auth_loaders.py
from flask_login import AnonymousUserMixin
from .extensions import login_manager, db

# Update this import to your actual User model location if different
try:
    from .models import User  # e.g., erp/models.py with class User(db.Model, UserMixin)
except Exception:  # pragma: no cover
    User = None  # Fallback to avoid import-time crashes in migrations

@login_manager.user_loader
def load_user(user_id):
    if not User:
        return None
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

@login_manager.request_loader
def load_user_from_request(request):
    # Optional: implement header/cookie based auth here if you need it
    return None

class _Anon(AnonymousUserMixin):
    pass

login_manager.anonymous_user = _Anon
