import importlib
import importlib.util
import os
from types import ModuleType
from typing import Optional

import pytest

redis_spec = importlib.util.find_spec("redis")
redis_lib: Optional[ModuleType]
if redis_spec:  # pragma: no cover - redis may be absent
    redis_lib = importlib.import_module("redis")  # type: ignore
else:  # pragma: no cover - redis not installed
    redis_lib = None


@pytest.mark.skipif(redis_lib is None, reason="redis-py not installed")
def test_redis_saturation():
    """Fill a Redis list to simulate saturation."""
    client = redis_lib.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"), port=6379, db=0
    )
    try:
        client.ping()
    except Exception:
        pytest.skip("Redis not available")
    payload = b"x" * 1024  # 1 KB payload
    for _ in range(100):
        client.lpush("chaos", payload)
    assert client.llen("chaos") == 100  # nosec B101
    client.delete("chaos")


