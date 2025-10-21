from prometheus_client import Gauge, Counter

# Tests poke these with ._value.set() / .get()
GRAPHQL_REJECTS = Gauge("graphql_rejects", "Rejected GraphQL queries")
RATE_LIMIT_REJECTIONS = Gauge("rate_limit_rejections", "Requests rejected by rate limits")
QUEUE_LAG = Gauge("queue_lag", "Broker queue depth", ["queue"])

# Must be a Counter so generate_latest() emits *_total
AUDIT_CHAIN_BROKEN = Counter("audit_chain_broken", "Audit chain break events")

# Used by scripts/olap_export.py and tests
OLAP_EXPORT_SUCCESS = Counter("olap_export_success", "Successful OLAP exports")
