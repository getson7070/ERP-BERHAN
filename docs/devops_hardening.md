# DevOps Hardening and Observability

- **Docker Security**: Containers run as non-root with pinned image digests and `HEALTHCHECK` probes.
- **Tracing**: OpenTelemetry exports traces to the collector at `OTEL_EXPORTER_OTLP_ENDPOINT`.
- **Status Page**: `/health` and `/metrics` endpoints back a public status dashboard.
- **Materialized View Freshness**: `scripts/alert_mv_staleness.py` emits alerts when refresh lag exceeds thresholds.
- **Deploy Strategy**: Canary releases with documented rollback steps in `docs/deploy.md`.
- **PgBouncer**: Connection pooling is enabled in production manifests with pgbouncer sidecars.
- **Soak & N+1 Tests**: CI runs soak tests nightly and `tests/test_query_efficiency.py` guards against N+1 queries.
- **GraphQL Complexity Middleware**: `middleware/graphql_complexity.py` enforces depth and cost limits.
- **Vault-based Secrets**: Application secrets load from HashiCorp Vault via `VAULT_ADDR` and `VAULT_TOKEN`.
- **Audit Chain Checker**: `scripts/check_audit_chain.py` validates cryptographic links in audit logs.
