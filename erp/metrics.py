"""
Super-light metric counters/gauges so tests can import expected names.
Keep everything in-process and thread-safe enough for tests.
"""
from __future__ import annotations
from threading import Lock

_lock = Lock()

# Counters that tests import from erp.metrics and sometimes from erp (re-exported in __init__)
RATE_LIMIT_REJECTIONS = 0
GRAPHQL_REJECTS = 0
# Gauge-ish value
QUEUE_LAG = 0.0

def inc_rate_limit_rejections(n: int = 1) -> None:
    global RATE_LIMIT_REJECTIONS
    with _lock:
        RATE_LIMIT_REJECTIONS += n

def inc_graphql_rejects(n: int = 1) -> None:
    global GRAPHQL_REJECTS
    with _lock:
        GRAPHQL_REJECTS += n

def set_queue_lag(value: float) -> None:
    global QUEUE_LAG
    with _lock:
        QUEUE_LAG = float(value)

# Cache metrics kept local to cache module as well, but expose helpers here if needed
def to_dict() -> dict:
    with _lock:
        return {
            "rate_limit_rejections": RATE_LIMIT_REJECTIONS,
            "graphql_rejects": GRAPHQL_REJECTS,
            "queue_lag": QUEUE_LAG,
        }