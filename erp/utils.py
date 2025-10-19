from __future__ import annotations
import json, functools
from flask import abort, request, session
from db import redis_client
from erp.metrics import RATE_LIMIT_REJECTIONS

def login_required(fn):  # safe no-op for tests without flask-login
    @functools.wraps(fn)
    def wrapper(*a, **k): return fn(*a, **k)
    return wrapper

def role_required(*roles):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            role = session.get("role")
            # simple hierarchy: Admin > Manager > Staff
            ranks = {"Admin": 3, "Manager": 2, "Staff": 1, None: 0}
            needed = max(ranks.get(r, 0) for r in roles) if roles else 0
            if ranks.get(role, 0) < needed:
                abort(403)
            return fn(*a, **k)
        return wrapper
    return deco

def mfa_required(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        if not session.get("mfa_verified"):
            abort(403)
        return fn(*a, **k)
    return wrapper

def idempotent(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        key = request.headers.get("Idempotency-Key")
        if not key:
            return fn(*a, **k)
        cache_key = f"idemp:{key}"
        if redis_client.get(cache_key):
            # record rate-limit-ish metric
            RATE_LIMIT_REJECTIONS.inc()
            abort(409, "Duplicate request")
        redis_client.set(cache_key, "1")
        return fn(*a, **k)
    return wrapper

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
