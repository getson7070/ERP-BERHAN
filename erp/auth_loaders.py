# erp/auth_loaders.py
from __future__ import annotations
from erp.extensions import login_manager, db
from erp.models import User


@login_manager.user_loader
def load_user(user_id: str):
    """
    Flask-Login callback: return a User or None.
    Works whether primary keys are int or str.
    """
    try:
        # If your User PK is UUID/str, remove the int() cast.
        return db.session.get(User, int(user_id))
    except Exception:
        try:
            return db.session.get(User, user_id)
        except Exception:
            return None


