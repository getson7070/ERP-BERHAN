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
    payload = json.dumps(entry)

    clients = []
    try:
        from erp.db import redis_client as c0
        if c0: clients.append(c0)
    except Exception:
        pass
    try:
        from db import redis_client as c1
        if c1 and all(c is not c1 for c in clients): clients.append(c1)
    except Exception:
        pass

    for cli in clients:
        for v in (payload, payload.encode("utf-8", "ignore")):
            try: cli.lpush("dead_letter", v)
            except Exception: pass