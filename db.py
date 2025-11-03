from __future__ import annotations
import os, json
from typing import Any, Optional
from sqlalchemy import create_engine

_engine = None
def _ensure_engine():
    global _engine
    if _engine is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            db_path = os.environ.get("DATABASE_PATH")
            url = f"sqlite+pysqlite:///{db_path}" if db_path else "sqlite+pysqlite:///:memory:"
        _engine = create_engine(url, future=True)
    return _engine

def get_db():
    return _ensure_engine().connect()

def get_engine():
    return _ensure_engine()

def get_dialect() -> str:
    return str(_ensure_engine().dialect.name)

class _MemRedis:
    def __init__(self) -> None:
        self.kv: dict[str, Any] = {}
    def get(self, key: str) -> Optional[Any]:
        return self.kv.get(key)
    def set(self, key: str, val: Any, ex: Optional[int] = None) -> None:
        self.kv[key] = val
    def delete(self, key: str) -> None:
        self.kv.pop(key, None)
    def lpush(self, key: str, *vals: Any) -> int:
        lst = self.kv.setdefault(key, [])
        for v in vals:
            lst.insert(0, v)
        return len(lst)
    def rpush(self, key: str, *vals: Any) -> int:
        lst = self.kv.setdefault(key, [])
        for v in vals:
            lst.append(v)
        return len(lst)
    def lrange(self, key: str, start: int, end: int) -> list:
        data = list(self.kv.get(key, []))
        stop = (end + 1) if end != -1 else None
        return data[start:stop]
    def llen(self, key: str) -> int:
        return len(self.kv.get(key, []))
    def sadd(self, key: str, val: Any) -> None:
        s = self.kv.setdefault(key, set())
        if isinstance(s, set):
            s.add(val)
        else:
            st = set(s); st.add(val); self.kv[key] = st
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
                url = os.environ.get("RATELIMIT_STORAGE_URI") or os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
                cli = redis.Redis.from_url(url, decode_responses=False)
                cli.ping()
                self.client = cli
                self.is_real = True
            except Exception:
                self.client = None
                self.is_real = False

    def get(self, key: str) -> Optional[bytes]:
        if self.client:
            try:
                return self.client.get(key)
            except Exception:
                pass
        v = self._mem.get(key)
        if v is None:
            return None
        return v if isinstance(v, (bytes, bytearray)) else str(v).encode()

    def set(self, key: str, val: Any, ex: Optional[int] = None) -> None:
        self._mem.set(key, val)
        if self.client:
            try:
                enc = val if isinstance(val, (bytes, bytearray)) else json.dumps(val).encode()
                self.client.set(key, enc, ex=ex)
            except Exception:
                pass

    def lpush(self, key: str, *vals: Any) -> int:
        self._mem.lpush(key, *vals)
        if self.client:
            try:
                enc = [v if isinstance(v, (bytes, bytearray)) else json.dumps(v).encode() for v in vals]
                self.client.lpush(key, *enc)
            except Exception:
                pass
        return self._mem.llen(key)

    def rpush(self, key: str, *vals: Any) -> int:
        self._mem.rpush(key, *vals)
        if self.client:
            try:
                enc = [v if isinstance(v, (bytes, bytearray)) else json.dumps(v).encode() for v in vals]
                self.client.rpush(key, *enc)
            except Exception:
                pass
        return self._mem.llen(key)

    def lrange(self, key: str, start: int, end: int) -> list:
        if self.client:
            try:
                out = self.client.lrange(key, start, end)
                if out:
                    return out
            except Exception:
                pass
        return self._mem.lrange(key, start, end)

    def llen(self, key: str) -> int:
        if self.client:
            try:
                v = int(self.client.llen(key))
                if v:
                    return v
            except Exception:
                pass
        return self._mem.llen(key)

    def sadd(self, key: str, val: Any) -> None:
        self._mem.sadd(key, val)
        if self.client:
            try:
                enc = val if isinstance(val, (bytes, bytearray)) else json.dumps(val).encode()
                self.client.sadd(key, enc)
            except Exception:
                pass

    def sismember(self, key: str, val: Any) -> bool:
        if self.client:
            try:
                enc = val if isinstance(val, (bytes, bytearray)) else json.dumps(val).encode()
                return bool(self.client.sismember(key, enc))
            except Exception:
                pass
        return self._mem.sismember(key, val)

    def delete(self, key: str) -> None:
        self._mem.delete(key)
        if self.client:
            try:
                self.client.delete(key)
            except Exception:
                pass

redis_client = _RedisClient()
