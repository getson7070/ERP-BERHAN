from __future__ import annotations
import os, json
from typing import Any

# ---- Resilient Redis wrapper (unchanged) ----
class _MemRedis:
    def __init__(self) -> None:
        self.kv: dict[str, Any] = {}

    def _as_list(self, key: str) -> list:
        v = self.kv.get(key)
        if isinstance(v, list):
            return v
        lst = list(v) if isinstance(v, (set, tuple)) else ([] if v is None else [v])
        self.kv[key] = lst
        return lst

    def delete(self, key: str) -> None:
        self.kv.pop(key, None)

    def lpush(self, key: str, *vals: Any) -> int:
        lst = self._as_list(key)
        for v in vals:
            lst.insert(0, v)
        return len(lst)

    def rpush(self, key: str, *vals: Any) -> int:
        lst = self._as_list(key)
        for v in vals:
            lst.append(v)
        return len(lst)

    def lrange(self, key: str, start: int, end: int) -> list:
        data = list(self._as_list(key))
        stop = (end + 1) if end != -1 else None
        return data[start:stop]

    def llen(self, key: str) -> int:
        return len(self._as_list(key))

    def sadd(self, key: str, val: Any) -> None:
        s = self.kv.get(key)
        if not isinstance(s, set):
            s = set()
            self.kv[key] = s
        s.add(val)

    def sismember(self, key: str, val: Any) -> bool:
        s = self.kv.get(key)
        return isinstance(s, set) and (val in s)

class _RedisClient:
    def __init__(self) -> None:
        self.is_real = False
        self.client = None
        self._mem = _MemRedis()
        use_fake = os.environ.get("USE_FAKE_REDIS", "").strip() == "1"
        if not use_fake:
            try:
                import redis  # type: ignore
                url = os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
                cli = redis.Redis.from_url(url, decode_responses=False)
                cli.ping()
                self.client = cli
                self.is_real = True
            except Exception:
                self.client = None
                self.is_real = False

    def lpush(self, key: str, *vals: Any) -> int:
        if self.client:
            try:
                enc = [v if isinstance(v, (bytes, bytearray)) else json.dumps(v).encode() for v in vals]
                return int(self.client.lpush(key, *enc))
            except Exception:
                pass
        return self._mem.lpush(key, *vals)

    def rpush(self, key: str, *vals: Any) -> int:
        if self.client:
            try:
                enc = [v if isinstance(v, (bytes, bytearray)) else json.dumps(v).encode() for v in vals]
                return int(self.client.rpush(key, *enc))
            except Exception:
                pass
        return self._mem.rpush(key, *vals)

    def lrange(self, key: str, start: int, end: int) -> list:
        if self.client:
            try:
                return self.client.lrange(key, start, end)
            except Exception:
                pass
        return self._mem.lrange(key, start, end)

    def llen(self, key: str) -> int:
        if self.client:
            try:
                return int(self.client.llen(key))
            except Exception:
                pass
        return self._mem.llen(key)

    def sadd(self, key: str, val: Any) -> None:
        if self.client:
            try:
                self.client.sadd(key, val if isinstance(val, (bytes, bytearray)) else json.dumps(val).encode())
                return
            except Exception:
                pass
        self._mem.sadd(key, val)

    def sismember(self, key: str, val: Any) -> bool:
        if self.client:
            try:
                return bool(self.client.sismember(key, val if isinstance(val, (bytes, bytearray)) else json.dumps(val).encode()))
            except Exception:
                pass
        return self._mem.sismember(key, val)

    def delete(self, key: str) -> None:
        if self.client:
            try:
                self.client.delete(key)
                return
            except Exception:
                pass
        self._mem.delete(key)

redis_client = _RedisClient()

# ---- Minimal ORM compatibility surface for test imports ----
# These are *placeholders* so pytest can import modules during collection.
# Real models/SQLAlchemy binding should live elsewhere; this prevents ImportError.
class _DB:  # simple namespace stub
    pass

db = _DB()

class User:          # placeholder model
    pass

class Inventory:     # placeholder model
    pass

class UserDashboard: # placeholder model
    pass

__all__ = ["redis_client", "db", "User", "Inventory", "UserDashboard"]