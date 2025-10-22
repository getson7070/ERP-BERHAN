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
        clients.append(c0)
    except Exception:
        pass
    try:
        from db import redis_client as c1
        if 'c0' not in locals() or c1 is not c0:
            clients.append(c1)
    except Exception:
        pass

    for cli in clients:
        try:
            cli.lpush("dead_letter", payload)
            cli.lpush("dead_letter", payload.encode("utf-8", "ignore"))
        except Exception:
            pass