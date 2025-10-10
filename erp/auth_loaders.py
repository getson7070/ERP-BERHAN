# erp/auth_loaders.py
# Minimal loaders so anonymous requests don't 500.
from flask_login import AnonymousUserMixin
from .extensions import login_manager

class _Anonymous(AnonymousUserMixin):
    pass

# Use a safe anonymous user object for visitors
login_manager.anonymous_user = _Anonymous

# Required by Flask-Login; return None if no such user
@login_manager.user_loader
def load_user(user_id: str):
    # TODO: integrate your real User model here, e.g.:
    # from .models import User
    # return User.query.get(user_id)
    return None

# Optional: allow token/header based auth in the future
@login_manager.request_loader
def load_user_from_request(request):
    # Return None to keep user anonymous by default
    return None
