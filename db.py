# db.py (root) – thin re-export shim to avoid old import paths breaking
from erp.db import (  # re-export real implementations
    get_db,
    redis_client,
)

__all__ = ["get_db", "redis_client"]
