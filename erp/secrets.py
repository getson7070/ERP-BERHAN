import json
import os
from threading import RLock
from typing import Any

_cache: dict[str, Any] = {}
_lock = RLock()


def get_secret(key: str) -> str | None:
    """Return secret value from a JSON vault file or environment variable.

    The vault file path is supplied via the ``VAULT_FILE`` environment
    variable.
    Secrets are reloaded automatically if the file changes to support rotation
    without restarting the application.
    """
    path = os.environ.get("VAULT_FILE")
    if not path:
        return os.environ.get(key)
    with _lock:
        mtime = os.path.getmtime(path)
        if _cache.get("_mtime") != mtime:
            with open(path) as fh:
                _cache.clear()
                _cache.update(json.load(fh))
                _cache["_mtime"] = mtime
        return _cache.get(key, os.environ.get(key))
