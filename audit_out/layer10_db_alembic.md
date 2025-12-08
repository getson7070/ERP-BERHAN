# Layer 10 Audit – Database Schema & Alembic (High-Level)

## Scope
Review migration wiring, metadata discovery, and standards for schema evolution relative to requirements (RBAC, geo, procurement, reporting).

## Current Capabilities
- **Alembic environment configuration**: `alembic/env.py` bootstraps metadata discovery from `erp.extensions.db`, supports offline/online runs, and configures compare_type/server_default for drift detection with environment-driven DB URL.【F:alembic/env.py†L1-L85】
- **Metadata discovery fallback**: Env file attempts multiple modules then honors `ALEMBIC_METADATA` override to locate SQLAlchemy metadata, reducing migration failures when refactoring structure.【F:alembic/env.py†L26-L53】
- **Migration inventory**: Repository contains consolidated migration docs and TODOs (MIGRATIONS_README/TODO) indicating awareness of schema gaps; tables include procurement, geo, analytics models referenced in services.
- **Recent migrations**: Org-scoped Telegram chat binding for users now ships with a merge-aware migration to keep bot security aligned with tenant boundaries and active session checks.【F:migrations/versions/e1f9a41f2f2c_add_org_and_telegram_to_users.py†L1-L36】

## Gaps & Risks vs. Requirements
- **Schema coverage**: Need verification that clients/employees/admins, MFA, commission, geo audit, procurement milestones, performance KPIs, and Telegram tokens are all modeled; current audit did not find dedicated MFA/commission tables.
- **Standards & constraints**: Unique constraints for TIN, multi-contact institutions, foreign keys for geo/event audit, and soft-delete policies need confirmation; retention policies not encoded.
- **Migration hygiene**: No automated migration ordering/linters; consolidation notes suggest potential drift risk without consistent stamping and down revisions.
- **Seed data**: Role catalog/KPI registry/geo consent defaults not seeded; onboarding may fail without initial data.

## Recommendations
1. **Schema gap analysis** against requirements (TIN uniqueness, multi-contact clients, MFA, commissions, geo audit, procurement milestones) and author migrations to close gaps.
2. **Enforce constraints** (unique indexes, foreign keys, check constraints for 10-digit TIN, geo coordinate bounds) and soft-delete/versioning where needed.
3. **Migration discipline**: Enable migration linting, auto-generation with review, and CI checks for drift; document upgrade paths in README-DEPLOY.
4. **Seed data migrations** for roles, KPI catalog, marketing consent defaults, and supervisor/admin records; ensure idempotent seeds.
5. **DB performance & security**: Partition high-volume tables (geo pings/logs), add auditing triggers, and ensure least-privilege DB roles; keep backups/SLA documented.

## Recent progress
- Added a critical health check that verifies the running database revision against the latest Alembic head, with safe skips in testing/ALLOW_INSECURE_DEFAULTS flows and strict opt-in for CI or production diagnostics. This closes a key readiness gap by surfacing drift early through `/health`/`/readyz` without breaking local dev.
