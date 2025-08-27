"""Caching utilities backed by Redis.

Provides a :class:`flask_caching.Cache` instance and helpers to invalidate
keys following the conventions documented in ``docs/cache_invalidation.md``.
"""
from __future__ import annotations

import os
import fnmatch
from flask_caching import Cache

cache = Cache()


def init_cache(app) -> None:
    """Initialise cache extension for *app*.

    When ``app.testing`` is True a simple in-memory backend is used so tests
    do not require a running Redis instance.
    """
    config = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    }
    if app.config.get("TESTING"):
        config = {"CACHE_TYPE": "SimpleCache"}
    cache.init_app(app, config=config)


def cache_set(key: str, value, ttl: int | None = None) -> None:
    """Store *value* under *key* for ``ttl`` seconds."""
    cache.set(key, value, timeout=ttl)


def cache_get(key: str):
    """Return cached value for *key* if present."""
    return cache.get(key)


def cache_invalidate(pattern: str) -> None:
    """Remove all keys matching *pattern* from the active backend."""
    backend = cache.cache  # type: ignore[attr-defined]
    if hasattr(backend, "_write_client"):
        client = backend._write_client
        for key in client.scan_iter(pattern):
            client.delete(key)
    elif hasattr(backend, "_cache"):
        # Fallback for SimpleCache used during tests
        for key in list(backend._cache.keys()):  # type: ignore[attr-defined]
            if fnmatch.fnmatch(key, pattern):
                backend.delete(key)
