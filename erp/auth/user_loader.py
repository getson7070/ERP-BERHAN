from typing import Optional
from ..extensions import login_manager

try:
    from ..models import User  # adjust this import if your User model lives elsewhere
except Exception:
    User = None  # type: ignore

@login_manager.user_loader
def load_user(user_id: str) -> Optional[object]:
    if User is None:
        return None
    try:
        # SQLAlchemy typical pattern; adjust to your ORM if needed
        return User.query.get(user_id)  # type: ignore[attr-defined]
    except Exception:
        return None


