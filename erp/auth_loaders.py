# erp/auth_loaders.py
from __future__ import annotations
from erp.extensions import login_manager, db
from erp.models import User

@login_manager.user_loader
def load_user(user_id: str):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None
