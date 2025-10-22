from __future__ import annotations
import json

def _dead_letter_handler(sender, task_id: str, exception: Exception, args: tuple, kwargs: dict) -> None:
    # Use the exact client the tests use.
    from db import redis_client
    entry = {
        "task": getattr(sender, "name", getattr(sender, "__name__", str(sender))),
        "task_id": task_id,
        "error": str(exception),
        "args": args,
        "kwargs": kwargs,
    }
    payload = json.dumps(entry).encode("utf-8", "ignore")
    # Left-push so newest appears first; tests only assert non-empty, so either would pass.
    redis_client.lpush("dead_letter", payload)