import sys

import pytest
import redis


def test_redis_connection_failure(monkeypatch):
    monkeypatch.delenv("USE_FAKE_REDIS", raising=False)

    class DummyRedis:
        def ping(self):
            raise redis.exceptions.ConnectionError

    monkeypatch.setattr(
        redis,
        "Redis",
        type("_Dummy", (), {"from_url": staticmethod(lambda url: DummyRedis())}),
    )
    sys.modules.pop("db", None)
    import db  # noqa: F401
    with pytest.raises(RuntimeError):
        db.redis_client.ping()


