# Registers a collector to expose graphql_rejects_total in the default Prometheus REGISTRY.
from __future__ import annotations

try:
    from prometheus_client.core import GaugeMetricFamily, REGISTRY
except Exception:  # prometheus_client not present in some envs; quietly skip
    REGISTRY = None
    GaugeMetricFamily = None

def _current_graphql_rejects() -> float:
    try:
        # Import inside function so it tracks the same module instance as the app.
        from erp.api.integrations import GRAPHQL_REJECTS
        return float(getattr(GRAPHQL_REJECTS._value, "val", 0.0))
    except Exception:
        return 0.0

class _GraphQLRejectsCollector:
    def collect(self):
        if GaugeMetricFamily is None:
            return []
        g = GaugeMetricFamily(
            "graphql_rejects_total",
            "Total rejected GraphQL queries (depth/complexity/auth)",
        )
        g.add_metric([], _current_graphql_rejects())
        return [g]

# Register once (ignore duplicate registrations when tests reload)
if REGISTRY is not None:
    try:
        REGISTRY.register(_GraphQLRejectsCollector())
    except ValueError:
        # Already registered
        pass