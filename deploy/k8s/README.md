# Kubernetes Manifests

This directory contains manifests for deploying the ERP system.

- `deployment.yaml` defines the web application with health probes.
- `hpa.yaml` configures horizontal pod autoscaling with a CPU target of 80% between 3 and 10 replicas. Monitor queue depth and materialized-view age in the [Grafana dashboard](https://example.com/grafana/erp).

Refer to `docs/deployment.md` for failover, rolling upgrade, and load-testing practices.
