# Centralized user_loader registration. If you have a User model, wire it here.
from typing import Optional
try:
    from ..models import User  # adjust import if your User model lives elsewhere
except Exception:
    User = None  # type: ignore

def register_user_loader(login_manager):
    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[object]:
        if User is None:
            return None
        try:
            # Adjust to your ORM; typical SQLAlchemy pattern:
            return User.query.get(user_id)  # type: ignore[attr-defined]
        except Exception:
            return None
