from __future__ import annotations
from typing import Any
import json

def _dead_letter_handler(sender: Any, task_id: str, exception: Exception, args: tuple, kwargs: dict) -> None:
    entry = {
        "task": getattr(sender, "name", getattr(sender, "__name__", str(sender))),
        "task_id": task_id,
        "error": str(exception),
        "args": args,
        "kwargs": kwargs,
    }
    payload_b = json.dumps(entry).encode("utf-8")

    try:
        from erp.db import redis_client
    except Exception:
        try:
            from db import redis_client
        except Exception:
            redis_client = None

    if not redis_client:
        return

    try:
        redis_client.lpush("dead_letter", payload_b)
        return
    except Exception:
        pass
    try:
        redis_client.lpush("dead_letter", payload_b.decode("utf-8", "ignore"))
    except Exception:
        pass
