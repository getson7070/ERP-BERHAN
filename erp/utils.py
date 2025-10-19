import hashlib
from functools import wraps
from typing import Callable, Iterable, Any
from flask import g, abort, request
try:
    from argon2 import PasswordHasher  # type: ignore
    _ph = PasswordHasher()
    def hash_password(pw: str) -> str:
        return _ph.hash(pw)
    def verify_password(hashval: str, pw: str) -> bool:
        try:
            return _ph.verify(hashval, pw)
        except Exception:
            return False
except Exception:  # pragma: no cover
    def hash_password(pw: str) -> str:
        return hashlib.sha256(pw.encode("utf-8")).hexdigest()
    def verify_password(hashval: str, pw: str) -> bool:
        return hash_password(pw) == hashval

def roles_required(*roles: str):
    roles_set = set(roles)
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None) or getattr(g, "user", None)
            user_roles = set(getattr(user, "roles", []) or [])
            if roles_set and not (user_roles & roles_set):
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# ---- Idempotency helpers backed by the fake redis in db.py ----
from db import redis_client  # our shim

def task_idempotent(key_func: Callable[..., str] | str, ttl: int = 300):
    def deco(fn):
        @wraps(fn)
        def inner(*a, **k):
            key = key_func(*a, **k) if callable(key_func) else str(key_func)
            rkey = f"idemp:task:{key}"
            if not redis_client.setnx(rkey, "1"):
                # Already running or completed recently
                return None
            redis_client.expire(rkey, ttl)
            return fn(*a, **k)
        return inner
    return deco

def idempotency_key_required(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        key = request.headers.get("Idempotency-Key") or request.headers.get("X-Idempotency-Key")
        if not key:
            abort(400, "Missing Idempotency-Key")
        rkey = f"idemp:req:{key}"
        if not redis_client.setnx(rkey, "1"):
            abort(409, "Duplicate request")
        redis_client.expire(rkey, 300)
        return fn(*a, **k)
    return wrapper

def has_permission(user: Any, perm: str) -> bool:
    if user is None:
        return False
    if getattr(user, "is_admin", False):
        return True
    perms = set(getattr(user, "permissions", []) or [])
    roles = set(getattr(user, "roles", []) or [])
    return perm in perms or ("admin" in roles)
# ---- auth decorator export ----
from typing import Callable, Any
try:
    # Prefer Flask-Login's decorator if available
    from flask_login import login_required as login_required  # re-export
except Exception:
    # No-op fallback so imports (and tests) don't crash in minimal envs
    def login_required(func: Callable | None = None, **kwargs: Any):
        def _decorator(f: Callable) -> Callable:
            return f
        return _decorator if func is None else func
# ---- /auth decorator export ----
# ---- auth decorator export ----
from typing import Callable, Any
try:
    # Prefer Flask-Login's decorator if available
    from flask_login import login_required as login_required  # re-export
except Exception:
    # No-op fallback so imports (and tests) don't crash in minimal envs
    def login_required(func: Callable | None = None, **kwargs: Any):
        def _decorator(f: Callable) -> Callable:
            return f
        return _decorator if func is None else func
# ---- /auth decorator export ----
# ---- sanitize helpers ----
def sanitize_direction(value: str | None, default: str = "asc") -> str:
    v = (value or "").strip().lower()
    if v in ("asc", "ascending", "+", "1", "up"):
        return "asc"
    if v in ("desc", "descending", "-", "-1", "down"):
        return "desc"
    return default
# ---- /sanitize helpers ----
# ---- sort sanitize helper ----
def sanitize_sort(
    value: str | None,
    allowed: list[str] | set[str] | tuple[str, ...] | None = None,
    default: str = "created_at",
) -> str:
    import re
    v = (value or "").strip()
    # allow only letters, digits, underscore and dot (for joined columns like org.name)
    v_clean = re.sub(r"[^A-Za-z0-9_\.]", "", v)
    if not v_clean:
        return default
    if allowed:
        return v_clean if v_clean in allowed else default
    return v_clean or default
# ---- /sort sanitize helper ----
# ---- CSV stream export helper ----
def stream_export(rows, filename: str = "export.csv", headers=None, mimetype: str = "text/csv"):
    """
    Stream a CSV download.
    - rows: iterable/generator of dicts or sequences
    - headers: optional header list; if omitted and rows are dicts, use first row's keys
    """
    from flask import Response, stream_with_context
    import csv, io

    def _iter_rows():
        nonlocal headers
        it = iter(rows)
        try:
            first = next(it)
        except StopIteration:
            first = None

        buf = io.StringIO(newline="")
        writer = csv.writer(buf)

        # Derive headers for dict rows if not provided
        if headers is None and isinstance(first, dict):
            headers = list(first.keys())

        # Write header row (if any)
        if headers:
            writer.writerow(headers)
            yield buf.getvalue()
            buf.seek(0); buf.truncate(0)

        def _emit(r):
            if isinstance(r, dict):
                if headers:
                    writer.writerow([r.get(h, "") for h in headers])
                else:
                    writer.writerow(list(r.values()))
            else:
                writer.writerow(list(r))

        if first is not None:
            _emit(first)
            yield buf.getvalue()
            buf.seek(0); buf.truncate(0)

        for r in it:
            _emit(r)
            out = buf.getvalue()
            if out:
                yield out
                buf.seek(0); buf.truncate(0)

    return Response(
        stream_with_context(_iter_rows()),
        mimetype=mimetype,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
# ---- /CSV stream export helper ----
# ---- robust login_required wrapper ----
# Use Flask-Login's decorator only if its extension is initialized.
def login_required(func=None, **kwargs):
    try:
        import flask_login
        from flask import current_app

        def _apply(f):
            try:
                lm = getattr(current_app, "extensions", {}).get("login_manager")
            except Exception:
                lm = None
            if getattr(flask_login, "login_required", None) and lm:
                return flask_login.login_required(f)
            return f

        return _apply if func is None else _apply(func)
    except Exception:
        # Flask-Login not installed: act as a no-op decorator
        return (lambda f: f) if func is None else func
# ---- /robust login_required wrapper ----
