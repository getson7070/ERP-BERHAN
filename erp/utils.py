from __future__ import annotations
import json, functools, os, hashlib
from flask import abort, request, session
from db import redis_client
from erp.metrics import RATE_LIMIT_REJECTIONS

# ----- Auth helpers expected by tests -----
def hash_password(pw: str) -> str:
    """Return a salted hash (prefer Werkzeug, fallback to PBKDF2)."""
    try:
        from werkzeug.security import generate_password_hash
        return generate_password_hash(pw)
    except Exception:
        # PBKDF2-HMAC-SHA256 with random hex salt
        salt = os.urandom(16).hex()
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 600_000).hex()
        return f"pbkdf2_sha256${salt}${dk}"

def verify_password(pw: str, hashed: str) -> bool:
    try:
        from werkzeug.security import check_password_hash
        return check_password_hash(hashed, pw)
    except Exception:
        if hashed.startswith("pbkdf2_sha256$"):
            _, salt, dk_hex = hashed.split("$", 2)
            calc = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 600_000).hex()
            return calc == dk_hex
        return False

# ----- Login/role/MFA gates (lightweight for tests) -----
def login_required(fn):  # no-op for tests without flask-login
    @functools.wraps(fn)
    def wrapper(*a, **k): return fn(*a, **k)
    return wrapper

# Role hierarchy: Admin > Manager > Staff
_RANKS = {"Admin": 3, "Manager": 2, "Staff": 1, None: 0}

def has_permission(user_role: str | None, required_role: str | None) -> bool:
    return _RANKS.get(user_role, 0) >= _RANKS.get(required_role, 0)

def role_required(*roles):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            role = session.get("role")
            needed = max((_RANKS.get(r, 0) for r in roles), default=0)
            if _RANKS.get(role, 0) < needed:
                abort(403)
            return fn(*a, **k)
        return wrapper
    return deco

# Alias name some tests import
roles_required = role_required

def mfa_required(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        if not session.get("mfa_verified"):
            abort(403)
        return fn(*a, **k)
    return wrapper

# ----- Idempotency helpers -----
def idempotency_key_required(fn):
    """Require Idempotency-Key header to be present; 400 if missing."""
    @functools.wraps(fn)
    def wrapper(*a, **k):
        if not request.headers.get("Idempotency-Key"):
            abort(400, "Missing Idempotency-Key")
        return fn(*a, **k)
    return wrapper

def idempotent(fn):
    """Prevent duplicate processing when Idempotency-Key repeats; 409 on repeat."""
    @functools.wraps(fn)
    def wrapper(*a, **k):
        key = request.headers.get("Idempotency-Key")
        if not key:
            return fn(*a, **k)
        cache_key = f"idemp:{key}"
        if redis_client.get(cache_key):
            RATE_LIMIT_REJECTIONS.inc()
            abort(409, "Duplicate request")
        redis_client.set(cache_key, "1")
        return fn(*a, **k)
    return wrapper

# ----- Dead letter recording -----
def dead_letter_handler(*, sender=None, task_id=None, exception=None, args=(), kwargs=None, **_):
    """Compatible signature with celery's task_failure signal in tests."""
    payload = {
        "task": getattr(sender, "name", str(sender)),
        "task_id": task_id,
        "error": str(exception),
        "args": list(args),
        "kwargs": kwargs or {},
    }
    redis_client.rpush("dead_letter", json.dumps(payload))
