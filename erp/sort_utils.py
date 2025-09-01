ALLOWED_DIRECTIONS = {"asc", "desc"}

def sanitize_sort(sort: str, allowed: set[str], default: str = "id") -> str:
    """Return sort if allowed else default."""
    return sort if sort in allowed else default


def sanitize_direction(direction: str, default: str = "asc") -> str:
    """Return direction if it's "asc" or "desc" else default."""
    return direction if direction in ALLOWED_DIRECTIONS else default
