# Observability SLOs

- **Latency:** 95% of requests < 300ms.
- **Error rate:** < 1% HTTP 5xx.
- **Queue lag:** alert if backlog > 100 jobs for 5 minutes.
- **Materialized view staleness:** refresh older than 15 minutes triggers warning.
- **Token errors:** sudden spikes in `token_errors_total` signal auth issues.

Configure Prometheus alerts for these SLOs and review dashboards weekly.
