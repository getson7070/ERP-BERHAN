# db.py (project root) — compatibility shim
# Keep older imports (from db import get_db) and newer ones
# (get_engine, ensure_schema, RedisClient, redis_client) working.

from erp.db import (  # re-export real implementations
    get_db,
    get_engine,
    ensure_schema,
    RedisClient,
    redis_client,
)

__all__ = ["get_db", "get_engine", "ensure_schema", "RedisClient", "redis_client"]
