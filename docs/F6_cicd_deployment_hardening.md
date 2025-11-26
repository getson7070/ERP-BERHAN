# F6 — CI/CD & Deployment Hardening (No-Surprise Releases)

## Objective
Every deployment must run a known image built from a known commit, against a known database schema, with predictable rollback and environment parity across local, staging, and production.

## Pipeline Guarantees (GitHub Actions)
1. **Job graph**: `lint-and-test` → `docker-build` → `publish-image` (GHCR) → `deploy` (only after publish).
2. **Image tagging**: publish `erp-berhan:<git_sha>` plus moving aliases (`:prod`, `:staging`).
3. **Build metadata**: embed `BUILD_SHA`, `BUILD_DATE`, `BUILD_ACTOR`; expose via `/version` endpoint for runtime verification.

## Environment Profiles
- Config classes: `LocalConfig`, `TestConfig`, `StagingConfig`, `ProductionConfig` selected by `ERP_ENV=local|test|staging|production` only.
- Compose split: `docker-compose.local.yml` (dev mounts, debug) vs `docker-compose.prod.yml` (no mounts, gunicorn, prod-like layout).
- Staging uses `ProductionConfig` defaults with isolated infra endpoints to minimize drift.

## Migration Safety Net (Alembic)
- CI fails on multiple heads: run `alembic history` and `alembic heads`.
- Add `tools/migrations_smoke.py`: create temp DB, apply migrations base→head, run minimal model smoke checks.
- Every migration declares contract: `safe_online`, `requires_maintenance_window`, or `destructive`; paired doc entry enforced by existing checks.

## Pre-Deploy Checklist Script
`tools/predeploy_check.py --env=production` verifies:
- Latest `main` SHA is green in CI; deploy workflow gated on green status.
- Single Alembic head.
- Required prod env vars present (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `TELEGRAM_BOTS_JSON`, etc.).
- Staging health checks passing.

## Health / Readiness / Liveness Endpoints
- `/healthz`: process up, basic self-checks; no DB/Redis dependency.
- `/readyz`: DB + Redis reachable, migrations at head, critical feature toggles sane.
- `/livez` (optional): confirms main loop/worker heartbeat for Kubernetes/Render probes.

## Rollback Strategy
- Image rollback: track old/new images; repoint `:prod` tag to previous SHA and redeploy.
- Migration policy: destructive migrations require backups; migrations must provide downgrade or be explicitly marked `no_downgrade` with justification.
- Runbook: extend `/docs/runbooks/deploy.md` with copy-paste rollback steps.

## Error Budget & Deploy Freeze
- Define error budget (e.g., ≤0.5% 5xx weekly). Exceeding budget blocks deploy job and requires incident review + fix before resuming releases.

## Operational Ownership Questions
- Is staging truly production-parity (flags, seeds, infra)?
- Who owns predeploy checklist, migrations, and rollback runbooks?
- Are rollbacks practiced regularly, not just documented?

