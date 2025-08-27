from erp import create_app
from erp.cache import cache_set, cache_get, CACHE_HITS, CACHE_MISSES


def test_cache_hit_miss_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'test.db'}")
    app = create_app()
    with app.app_context():
        cache_set("foo", "bar")
        cache_get("foo")
        cache_get("missing")
    assert CACHE_HITS._value.get() >= 1
    assert CACHE_MISSES._value.get() >= 1
