# Kubernetes Manifests

This directory contains manifests for deploying the ERP system.

- `deployment.yaml` defines the web application with health probes.
- `hpa.yaml` configures horizontal pod autoscaling to keep CPU at 70%.
  Pods scale between 3 and 10 replicas when average CPU exceeds the threshold.
- `prometheus.yaml` and `service.yaml` expose metrics for monitoring.

A Grafana dashboard (link placeholder) visualises queue depth and materialised view age.
Refer to `docs/deployment.md` for failover, rolling upgrade, and load-testing practices.
