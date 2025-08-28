# Observability SLOs

- **Latency:** 95% of requests < 300ms.
- **Error rate:** < 1% HTTP 5xx.
- **Queue lag:** alert if backlog > 100 jobs for 5 minutes.
- **Materialized view staleness:** refresh older than 15 minutes triggers warning.
- **Token errors:** sudden spikes in `token_errors_total` signal auth issues.
- **Cache hit rate:** alert if `cache_hit_rate` drops below 0.8 for 10 minutes.
- **Rate limiting:** monitor `429` counts to detect abusive clients.
- **Audit log integrity:** `audit_chain_broken_total` should remain `0`; any increase triggers incident response.
- **Tracing:** OpenTelemetry spans are exported via OTLP and surfaced in Grafana Tempo.
- **Status page:** `/status` aggregates health checks for use with external uptime monitors.
- **MV freshness alerts:** wire `kpi_sales_mv_age_seconds` into a Prometheus rule to page if the value exceeds 900 seconds.
- **Canary/rollback:** route a small percentage of traffic to new pods and follow `docs/rollback.md` if error budgets are exhausted.

Configure Prometheus alerts for these SLOs and review dashboards weekly.
