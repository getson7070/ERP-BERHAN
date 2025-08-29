# Deployment & Operations

## Failover Procedures
- Use Kubernetes readiness and liveness probes to automatically restart unhealthy pods.
- Maintain at least 3 replicas and rely on the cluster's service abstraction for failover.

## Rolling Upgrades
- Apply updates with `kubectl rollout restart deployment/erp-berhan`.
- Monitor rollout status and use `kubectl rollout undo` to roll back if necessary.

## Canary & Blue-Green
- For higher confidence releases, deploy a small canary slice or a full
blue-green environment before shifting all traffic. Monitor metrics and roll
forward or back based on health.

## Load Testing
- Execute `python scripts/benchmark.py` against the service URL to measure throughput.
- Scale test by adjusting `deploy/k8s/hpa.yaml` thresholds and replicas.

## CI/CD & Configuration
- A sample GitHub Actions workflow builds images, runs tests and security scans, and pushes to the registry on every commit.
- All configuration is supplied via environment variables to keep dev/stage/prod environments in parity.
- Feature flags can be toggled via the `feature_flags` table allowing safe rollouts and quick reversions.
- Secrets should be stored in a vault such as HashiCorp Vault and injected at runtime.

## Disaster Recovery
- The `docs/deployment/failover.md` and `docs/deployment/upgrade_rollback.md` outlines a full DR runbook.
- Dependency failures should degrade gracefully; Redis and database outages are logged and surfaced via Prometheus alerts.
