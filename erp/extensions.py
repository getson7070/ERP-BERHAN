from __future__ import annotations

# Reuse the single SQLAlchemy instance defined in erp.db
try:
    from .db import db  # shared instance
except Exception:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()

from flask_login import LoginManager
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

# --- Rate limiting ---
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address)  # init_app() called in create_app()
except Exception:
    # Fallback no-op so imports/decorators don't crash in minimal envs
    class _NoopLimiter:
        def limit(self, *a, **k):
            def deco(f): return f
            return deco
        def init_app(self, *a, **k): pass
    limiter = _NoopLimiter()
# --- /Rate limiting ---


