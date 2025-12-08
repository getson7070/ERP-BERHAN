# Layer 11 Audit – Deployment & Production Readiness

## Scope
Assess deployment guides, hardening defaults, and operational controls versus requirements for secure, production-ready rollout with MFA, RBAC, and observability.

## Current Capabilities
- **Deployment playbook**: README-DEPLOY documents environment setup, Docker Compose build/run, migration steps, blueprint freezing, and security toggles (CSRF, cookie hardening, CSP/HSTS option).【F:README-DEPLOY.md†L1-L38】
- **Windows/local guides**: Windows Docker Desktop walkthrough and helper scripts are provided for reproducible local deployments and snapshotting.【F:README-DEPLOY.md†L39-L58】

## Gaps & Risks vs. Requirements
- **MFA and admin hardening**: Deployment guide does not mandate MFA for admin/management logins or configure SSO/IdP integration; secrets management steps are not enforced.
- **Operational readiness**: Lacks documented health checks beyond `/healthz`, no SLA/uptime targets, incident response linkage, or monitoring/log forwarding requirements.
- **Security posture**: No baseline for rate limits, WAF/CDN, bot/webhook security, or dependency scanning in CI; container image hardening not specified.
- **Data protection**: Backup/restore, key rotation, and geo data retention policies are not encoded; encryption at rest/in transit assumptions not spelled out.
- **UX/stability across environments**: No explicit compatibility matrix for browsers/mobile or instructions for progressive rollouts and smoke tests after deploy.

## Recommendations
1. **Enforce MFA/SSO** for admin/supervisor roles at deployment; document IdP integration and session policies.
2. **Operational runbooks**: Add monitoring/alerting setup (APM, logs, metrics), SLAs, readiness/liveness probes, and incident response hooks tied to SRE runbooks.
3. **Security hardening**: Define rate limits, WAF/CDN guidance, webhook verification, secrets management, SBOM/dependency scanning, and container image hardening steps.
4. **Data resilience**: Document backups, restores, key rotation, retention for geo/personal data, and disaster recovery testing cadence.
5. **Post-deploy validation & UX**: Standardize smoke tests, browser/mobile compatibility checks, and accessibility/performance budgets to keep UX at industry standards.

## Recent progress
- Deployment readiness now includes migration drift detection exposed via the shared health endpoints, enabling probes to fail fast when the database is behind the Alembic head while still allowing safe skips in test/dev by default.
