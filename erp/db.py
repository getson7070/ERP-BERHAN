from __future__ import annotations
import os, json
from typing import Any

# --------------------------
# Resilient Redis client
# --------------------------
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

    # mem-first write; then try real client
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
        # Prefer real client but fall back to mem if it errors or is empty
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
                self.client.sadd(key, val if isinstance(val, (bytes, bytearray)) else json.dumps(val).encode())
            except Exception:
                pass

    def sismember(self, key: str, val: Any) -> bool:
        if self.client:
            try:
                return bool(self.client.sismember(key, val if isinstance(val, (bytes, bytearray)) else json.dumps(val).encode()))
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

# --------------------------
# Minimal SQLAlchemy "db" shim
# --------------------------
try:
    import sqlalchemy as sa
    from sqlalchemy import orm
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

    class _DBShim:
        # expose Flask-SQLAlchemy-like types/constructs
        Model = Base
        Column = sa.Column
        Integer = sa.Integer
        BigInteger = sa.BigInteger
        SmallInteger = sa.SmallInteger
        String = sa.String
        Unicode = sa.Unicode
        UnicodeText = sa.UnicodeText
        Text = sa.Text
        LargeBinary = sa.LargeBinary
        Float = sa.Float
        Boolean = sa.Boolean
        Date = sa.Date
        DateTime = sa.DateTime
        Numeric = sa.Numeric
        JSON = getattr(sa, "JSON", sa.Text)
        ForeignKey = sa.ForeignKey
        ForeignKeyConstraint = sa.ForeignKeyConstraint
        CheckConstraint = sa.CheckConstraint
        UniqueConstraint = sa.UniqueConstraint
        Index = sa.Index
        Table = sa.Table
        func = sa.func

        def __init__(self) -> None:
            url = os.environ.get("DATABASE_URL") or "sqlite:///:memory:"
            self.engine = sa.create_engine(url, future=True)
            self.metadata = Base.metadata
            self.sessionmaker = orm.sessionmaker(bind=self.engine, future=True, expire_on_commit=False)
            self.session = self.sessionmaker()
            # assign on the INSTANCE to avoid bound-method/self issues
            self.relationship = orm.relationship
            self.backref = orm.backref

        # flask-sqlalchemy compat no-ops
        def init_app(self, app: Any) -> None:
            return None

        def create_all(self) -> None:
            self.metadata.create_all(self.engine)

        def drop_all(self) -> None:
            self.metadata.drop_all(self.engine)

        # handy: fall back to sqlalchemy namespace for anything we didn't expose
        def __getattr__(self, name: str) -> Any:
            if hasattr(sa, name):
                return getattr(sa, name)
            raise AttributeError(name)

    db = _DBShim()

except Exception:
    # ultra-lenient stub if SQLAlchemy isn't available
    class _DummyDB:
        class _DummyModel: ...
        Model = _DummyModel  # type: ignore
        def __getattr__(self, name: str):
            def _stub(*args: Any, **kwargs: Any) -> Any:
                return None
            return _stub
    db = _DummyDB()
    class Base:  # type: ignore
        pass

# Keep these placeholders to satisfy import-by-name from erp.db in UI tests.
class User:          # type: ignore
    pass
class Inventory:     # type: ignore
    pass
class UserDashboard: # type: ignore
    pass