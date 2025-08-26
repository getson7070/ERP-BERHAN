import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp.cache import cache_set, cache_get, cache_invalidate


def test_cache_set_and_invalidate():
    cache_set('test:key', {'v': 1}, ttl=60)
    assert cache_get('test:key') == {'v': 1}
    cache_invalidate('test:*')
    assert cache_get('test:key') is None
