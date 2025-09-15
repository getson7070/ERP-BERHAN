# Observability Strategy

The platform exposes metrics, traces, and logs through Prometheus and OpenTelemetry. The `/status` page provides a live snapshot of the current SLO posture, error-budget burn, and links to the incident runbook and postmortem templates.

## Core SLO Catalogue

| Objective | Target | Window | Alerting Rules |
| --------- | ------ | ------ | -------------- |
| API availability | ≥ 99.9% success responses | 30 days | Page if burn rate ≥ 2× for 15 minutes or availability < 99.9% |
| Apdex (T = 0.5s) | ≥ 0.85 | Rolling | Warn if < 0.9 for 10 minutes, breach if < 0.85 |
| Celery backlog | ≤ 50 jobs (warn ≥ 75, breach ≥ 100) | Continuous | Scale workers if warning threshold sustained for 5 minutes |
| Sales MV freshness | ≤ 15 minutes (warn 20, breach 30) | Continuous | Trigger manual refresh task, investigate OLAP export |

Additional guardrail metrics:

- `token_errors_total` for authentication anomalies
- `audit_chain_broken_total` for data-integrity regressions
- `rate_limit_rejections_total` for abusive client behaviour

## OpenTelemetry Export

The Flask app auto-instruments when `OTEL_ENABLED=true` or an `OTEL_EXPORTER_OTLP_ENDPOINT` is provided. Configure exporters via environment variables:

```bash
export OTEL_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otel-collector.example.com/v1"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer <token>"
export OTEL_SERVICE_NAME="erp-berhan"
export OTEL_METRIC_EXPORT_INTERVAL=15  # seconds
export OTEL_EXPORT_TIMEOUT=10          # seconds
```

Instrumentation covers Flask, SQLAlchemy, Redis, Requests, and Celery. Logs include `trace_id` and `span_id` fields to correlate with spans. To verify locally:

```bash
poetry run flask routes   # warm up app
curl http://localhost:5000/healthz
otelcol --config config/otel-local.yaml  # collector with logging/exporters
```

## Prometheus Integration

Prometheus scrapes the web app, Celery workers, PgBouncer, and Redis using [`deploy/k8s/prometheus.yaml`](../deploy/k8s/prometheus.yaml). Ensure the following alerts are configured:

- `AvailabilityBurnRate` (2×/1h & 14×/5m pairs)
- `ApdexLow` (< 0.85 for 10m)
- `QueueBacklogHigh` (> 75 for 5m)
- `MaterializedViewStale` (> 20 minutes)
- `TokenErrorsSpike`

Dashboards should surface Apdex, availability, queue backlog, and MV freshness, matching the layout of the `/status` UI cards.

## Operational Runbooks

- [SRE Incident Runbook](SRE_RUNBOOK.md)
- [Postmortem Template](POSTMORTEM_TEMPLATE.md)
- [Disaster Recovery Plan](dr_plan.md)
- [Status Publishing Process](status.md)

Runbooks are reviewed quarterly; update them whenever alerts or automation change.

## Tooling & Automation

- `scripts/monitor_queue.py`: sidecar polling queue depth and `/healthz`
- `scripts/dr_drill.sh`: validates RPO/RTO assumptions during restore drills
- `scripts/rotate_secrets.py`: rotates database/API credentials with audit logging

All automation must emit OTEL traces and structured logs. Verify correlation IDs are propagated end-to-end during game days.
