from prometheus_client import Gauge, Counter

# Tests poke these with ._value.set() / .get()
GRAPHQL_REJECTS = Gauge("graphql_rejects", "Rejected GraphQL queries")
# Mirror so /metrics output contains `graphql_rejects_total <n>`
GRAPHQL_REJECTS_TOTAL = Gauge("graphql_rejects_total", "Total rejected GraphQL queries (mirror)")

RATE_LIMIT_REJECTIONS = Gauge("rate_limit_rejections", "Requests rejected by rate limits")
QUEUE_LAG = Gauge("queue_lag", "Broker queue depth", ["queue"])

# Must be a Counter so generate_latest() emits *_total (used elsewhere)
AUDIT_CHAIN_BROKEN = Counter("audit_chain_broken", "Audit chain break events")

# Used by scripts/olap_export.py and tests
OLAP_EXPORT_SUCCESS = Counter("olap_export_success", "Successful OLAP exports")