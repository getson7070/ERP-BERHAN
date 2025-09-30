# erp/db.py
import os
from dataclasses import dataclass

from redis import Redis
from erp.extensions import db as sqla_db

def get_db():
    """Return SQLAlchemy session (use db.session in your code)."""
    return sqla_db.session

@dataclass(frozen=True)
class _RedisClient:
    client: Redis | None
    is_real: bool

def _make_redis() -> _RedisClient:
    url = os.getenv("REDIS_URL")
    if not url:
        return _RedisClient(client=None, is_real=False)
    return _RedisClient(client=Redis.from_url(url), is_real=True)

redis_client = _make_redis()