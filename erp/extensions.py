from __future__ import annotations
from typing import Any, Callable

# CSRF
try:
    from flask_wtf import CSRFProtect  # type: ignore
    csrf: Any = CSRFProtect()
except Exception:  # minimal shim
    class _CSRF:
        def init_app(self, app: Any) -> None: ...
        def exempt(self, f: Callable) -> Callable: return f
    csrf = _CSRF()  # type: ignore

# Rate Limiter
try:
    from flask_limiter import Limiter  # type: ignore
    try:
        from flask_limiter.util import get_remote_address  # type: ignore
        limiter: Any = Limiter(key_func=get_remote_address, storage_uri=os.getenv("REDIS_URL","redis://cache:6379/0"))
    except Exception:
        limiter = Limiter()
except Exception:
    class _Limiter:
        def init_app(self, app: Any) -> None: ...
        def limit(self, *a: Any, **k: Any):
            def deco(f: Callable) -> Callable: return f
            return deco
        def request_filter(self, fn: Callable) -> Callable: return fn
    limiter = _Limiter()  # type: ignore

# Login manager (lightweight; some blueprints import this symbol)
try:
    from flask_login import LoginManager  # type: ignore
    login_manager: Any = LoginManager()
    login_manager.login_view = "web.login_page"
except Exception:
    class _LM:
        def init_app(self, app: Any) -> None: ...
        def user_loader(self, fn: Callable) -> Callable: return fn
    login_manager = _LM()  # type: ignore

# Expose SQLAlchemy-like db shim (backed by erp.db)
try:
    from .db import db  # type: ignore
except Exception:
    db = None  # type: ignore


