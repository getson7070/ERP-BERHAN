from typing import Any

_DLQ: list[dict[str, Any]] = []

def push_dead_letter(item: dict[str, Any]) -> None:
    _DLQ.append(item)

def dlq_length() -> int:
    return len(_DLQ)

def drain() -> list[dict[str, Any]]:
    out = list(_DLQ)
    _DLQ.clear()
    return out
