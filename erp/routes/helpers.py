from typing import Iterable


def sanitize_sort(sort: str, allowed: Iterable[str], default: str) -> str:
    """Return sort if allowed, else default."""
    return sort if sort in allowed else default


def sanitize_direction(direction: str, default: str = "asc") -> str:
    """Return direction if valid, else default."""
    return direction if direction in {"asc", "desc"} else default
