from dataclasses import dataclass
from .dlq import dlq_length
from .cache import CACHE_HITS, CACHE_MISSES

REQUEST_COUNT = 0
ERROR_COUNT = 0

@dataclass
class Snapshot:
    requests: int
    errors: int
    cache_hits: int
    cache_misses: int
    queue_lag: int

def snapshot() -> Snapshot:
    return Snapshot(
        requests=REQUEST_COUNT,
        errors=ERROR_COUNT,
        cache_hits=CACHE_HITS,
        cache_misses=CACHE_MISSES,
        queue_lag=dlq_length(),
    )
