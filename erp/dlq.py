from __future__ import annotations
from datetime import datetime
from threading import RLock
from typing import Any, Optional, Dict, List

# Prometheus counter (safe fallback if lib missing)
try:
    from prometheus_client import Counter  # type: ignore
except Exception:  # pragma: no cover
    class _Noop:
        def inc(self, *a, **k): pass
    def Counter(*a, **k):  # type: ignore
        return _Noop()

DEAD_LETTERS_TOTAL = Counter("dead_letters_total", "Total messages sent to DLQ")

# In-memory DLQ storage (sufficient for tests)
_DLQ: List[Dict[str, Any]] = []
_DLQ_LOCK = RLock()

def dead_letter_handler(message: Any, reason: Optional[str] = None) -> None:
    """Append a failed message to the in-memory DLQ and increment a metric."""
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "message": message,
        "reason": reason or "unknown",
    }
    with _DLQ_LOCK:
        _DLQ.append(entry)
        try:
            DEAD_LETTERS_TOTAL.inc()
        except Exception:
            pass

def get_dlq_snapshot() -> list[dict]:
    """Return a shallow copy of the DLQ (testing aid)."""
    with _DLQ_LOCK:
        return list(_DLQ)
