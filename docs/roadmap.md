# Project Roadmap

The following milestones outline upcoming development:

1. **Q1:** Complete remaining ERP modules (finance, HR, procurement, manufacturing, projects).
2. **Q2:** Deliver drag-and-drop reporting with anomaly detection and forecasting.
3. **Q3:** Launch plugin marketplace and additional bot adapters.
4. **Q4:** Achieve ISO 27001 alignment and conduct external security audit.

## Completed

- Containerisation with Docker Compose and Kubernetes manifests
- CI/CD pipeline with automated testing and blueprint validation
- Structured JSON logging with request IDs and health/ready probes (aligned with corporate SOP)

Progress is tracked in the issue tracker; update this roadmap each quarter for transparency.

## Audit Follow-Ups (Sep 2025)
- Unify authentication/authorization across all routes.
- Finish HR recruitment and performance workflows and wire them to the database layer.
- Replace raw SQL in routes with SQLAlchemy models or dedicated service objects.
- Stabilize the report builder with persistence, field whitelists, and feature flags.
- Add smoke tests and document user flows for new HR and dashboard pages.
- Create indices for common query filters and enable slow-query logging.
- Hide unfinished routes in navigation and apply role-based menu visibility.

## Phased Audit Remediation Plan

### Phase 1 – Developer Onboarding & Docs
- Publish [Local Development Quickstart](local_dev_quickstart.md) and env-var matrix
- Add ERD snapshots and migration guide refinements
- Gate pulls on README/AGENTS updates for new modules

### Phase 2 – Security Gates
- Make gitleaks, Bandit, pip-audit, Trivy and ZAP fail the build on critical findings
- Enforce signed commits and SBOM attestation in CI
- Document secret rotation cadence

### Phase 3 – Performance & UX
- Define p95 < 500 ms API budget with regression thresholds in `perf.yml`
- Expand pa11y/axe accessibility coverage and fix reported issues
- Add inline validation and empty-state copy to HR and Reports pages

### Phase 4 – Continuous Monitoring
- Track latency and error-rate trends; alert on budget breaches
- Schedule weekly dependency updates and vulnerability triage
- Quarterly review of database indices and slow-query logs
