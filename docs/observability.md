# Observability SLOs

- **Latency:** 95% of requests < 300ms.
- **Error rate:** < 1% HTTP 5xx.
- **Queue lag:** alert if backlog > 100 jobs for 5 minutes.
- **Materialized view staleness:** refresh older than 15 minutes triggers warning.
- **Token errors:** sudden spikes in `token_errors_total` signal auth issues.
- **Cache hit rate:** alert if `cache_hit_rate` drops below 0.8 for 10 minutes.
- **Rate limiting:** monitor `429` counts to detect abusive clients.

Configure Prometheus alerts for these SLOs and review dashboards weekly.
