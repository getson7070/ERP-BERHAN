try:
    from prometheus_client import Gauge, Counter  # type: ignore
except Exception:  # fallback when prometheus_client is missing
    class _NoopMetric:
        def labels(self, *a, **kw): return self
        def inc(self, *a, **kw):  ...
        def dec(self, *a, **kw):  ...
        def observe(self, *a, **kw):  ...
        def set(self, *a, **kw):  ...
    def Gauge(*a, **kw): return _NoopMetric()
    def Counter(*a, **kw): return _NoopMetric()

# Core metrics expected by tests
QUEUE_LAG = Gauge("erp_queue_lag_seconds", "Queue lag in seconds", ["queue"]) if callable(Gauge) else Gauge
RATE_LIMIT_REJECTIONS = Counter("erp_rate_limit_rejections_total", "Rate limit rejections")
GRAPHQL_REJECTS = Counter("erp_graphql_rejects_total", "GraphQL rejects")
AUDIT_CHAIN_BROKEN = Counter("erp_audit_chain_broken_total", "Audit chain broken")
DLQ_MESSAGES = Counter("erp_dead_letter_messages_total", "Dead-letter messages")

# Success sentinel expected by scripts/tests
OLAP_EXPORT_SUCCESS = "OLAP_EXPORT_SUCCESS"

def _dead_letter_handler(payload, *, reason: str = "unknown"):
    """
    Minimal DLQ handler to satisfy tests.
    Increments DLQ counter and returns a structured result.
    """
    try:
        DLQ_MESSAGES.inc()
    except Exception:
        pass
    return {"ok": True, "reason": reason}
