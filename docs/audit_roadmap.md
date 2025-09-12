# Audit Remediation Roadmap

This roadmap breaks the September 2025 audit findings into actionable phases. Each phase references BERHAN Pharma corporate policy and ISO-aligned practices to keep the ERP secure, compliant and easy to use.

## Phase 1 – Onboarding & Documentation
- Publish a **Local Development Quickstart** in the README with environment variables, migrations and a smoke test.
- Add an environment matrix (.env.example) describing dev/stage/prod feature flags and secrets locations.
- Capture ERD snapshots and migration notes for core modules.

## Phase 2 – Security Gates
- Make CI security scans fail-closed: gitleaks, Bandit, pip-audit, Trivy and ZAP must report no critical findings before merge.
- Enforce commit signing and CODEOWNERS review on every pull request.
- Rotate secrets per docs/security/secret_rotation.md and document incidents in the risk register.

## Phase 3 – UX & Data Quality
- Add inline validation, empty-state guidance and ARIA labels to HR and Reports pages.
- Publish database ERD and migration guides; prefer SQLAlchemy services over raw SQL.
- Run accessibility tests (Pa11y/axe) on each pull request and fix violations.

## Phase 4 – Performance & Monitoring
- Define performance budgets (e.g. API p95 < 500 ms) in `.github/workflows/perf.yml` and fail the build on regressions.
- Record performance artifacts for trending and expose metrics on the status page.
- Schedule dependency checks and accessibility audits to run weekly, surfacing results to the team.

Progress against this roadmap should be reviewed in the monthly Quality Management Review (QMR) and updated as milestones are completed.
