from __future__ import annotations
from typing import Any, Callable

# --- CSRF ---
try:
    from flask_wtf import CSRFProtect  # type: ignore
    csrf: Any = CSRFProtect()
except Exception:
    class _CSRF:
        def init_app(self, app: Any) -> None: ...
        def exempt(self, f: Callable) -> Callable:  # used as @csrf.exempt
            return f
    csrf = _CSRF()

# --- Rate Limiter ---
try:
    from flask_limiter import Limiter  # type: ignore
    try:
        # v2 API prefers a key_func
        from flask_limiter.util import get_remote_address  # type: ignore
        limiter: Any = Limiter(key_func=get_remote_address)
    except Exception:
        # older API
        limiter = Limiter()
except Exception:
    class _Limiter:
        def __init__(self) -> None:
            self._filters = []
        def init_app(self, app: Any) -> None: ...
        def limit(self, *args: Any, **kwargs: Any):
            def deco(f: Callable) -> Callable:
                return f
            return deco
        def request_filter(self, fn: Callable) -> Callable:
            self._filters.append(fn)
            return fn
    limiter = _Limiter()

# --- Expose SQLAlchemy-like db shim for tests that import it here ---
try:
    from .db import db  # type: ignore
except Exception:
    db = None  # type: ignore