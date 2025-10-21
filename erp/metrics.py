from prometheus_client import Gauge, Counter

# Exposed metrics the tests poke with ._value.set()/get()
GRAPHQL_REJECTS = Gauge("graphql_rejects", "Rejected GraphQL queries")
RATE_LIMIT_REJECTIONS = Gauge("rate_limit_rejections", "Requests rejected by rate limits")
QUEUE_LAG = Gauge("queue_lag", "Broker queue depth", ["queue"])

# Keep a Gauge for test resets AND add a Counter so the scrape exposes *_total
AUDIT_CHAIN_BROKEN = Gauge("audit_chain_broken", "Audit chain break events")
AUDIT_CHAIN_BROKEN_TOTAL = Counter("audit_chain_broken_total", "Audit chain breaks total")
