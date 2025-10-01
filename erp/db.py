# erp/db.py
from __future__ import annotations
import os
from dataclasses import dataclass
from sqlalchemy import create_engine
from flask import current_app
from redis import Redis
from erp.extensions import db as sqla_db

def get_db():
    return sqla_db.session

def get_engine():
    url = os.getenv("DATABASE_URL") or current_app.config.get("SQLALCHEMY_DATABASE_URI")
    if not url:
        raise RuntimeError("DATABASE_URL/SQLALCHEMY_DATABASE_URI not configured")
    return create_engine(url, future=True)

@dataclass(frozen=True)
class _RedisClient:
    client: Redis | None
    is_real: bool

def _make_redis() -> _RedisClient:
    url = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL")
    if not url:
        return _RedisClient(client=None, is_real=False)
    return _RedisClient(client=Redis.from_url(url, decode_responses=True), is_real=True)

redis_client = _make_redis()
