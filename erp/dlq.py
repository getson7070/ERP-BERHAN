import json, time
from functools import wraps
from flask import request
from .cache import redis_client

def idempotent(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        key=request.headers.get("Idempotency-Key")
        if not key:
            return fn(*a, **k)
        token=f"idem:{key}"
        if redis_client.get(token):
            return ("", 409)
        redis_client.set(token, str(time.time()))
        return fn(*a, **k)
    return wrapper

def _dead_letter_handler(sender, task_id, exception, args, kwargs):
    entry={"sender": getattr(sender, "name", str(sender)), "task_id": task_id,
           "error": str(exception), "args": args, "kwargs": kwargs, "ts": time.time()}
    redis_client.lpush("dead_letter", json.dumps(entry))
