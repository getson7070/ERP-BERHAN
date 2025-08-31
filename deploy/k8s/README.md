# Kubernetes Manifests

This directory contains manifests for deploying the ERP system.

- `deployment.yaml` defines the web application with health probes.
- `hpa.yaml` configures horizontal pod autoscaling with a CPU target of 80% between 3 and 10 replicas. Monitor queue depth and materialized-view age in the [Grafana dashboard](https://example.com/grafana/erp).
- `pdb.yaml` adds a PodDisruptionBudget ensuring at least two application pods remain during voluntary disruptions.
- `pgbouncer.yaml` provisions the PgBouncer connection pooler with resource limits and readiness/liveness probes.
- `pgbouncer-pdb.yaml` keeps at least one PgBouncer replica available during voluntary disruptions.
- `prometheus.yaml` defines ServiceMonitors for the web app, Celery workers,
  PgBouncer, and Redis so metrics are scraped by Prometheus.

Refer to `docs/deployment.md` for failover, rolling upgrade, and load-testing practices.
