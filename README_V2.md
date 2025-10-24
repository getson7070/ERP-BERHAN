# ERP-BERHAN Phased Upgrades **V2** (Applied 2025-10-24 18:26:41 UTC)

**What’s new vs v1**
- Adds **/ops/doctor** (read-only) blueprint for DB, migrations, secrets-age, email smoke diagnostics.
- Adds **idempotent patchers** to auto-wire MFA and Doctor blueprints into your app factory if present.
- Makes **Alembic/CSP gates hard by default** (toggle with `PREDEPLOY_STRICT=0`).
- Adds **basic contract tests** (status + app-factory probe) to prove journeys immediately.
- Adds **branch-protection checklist** so the gates are enforced.

Safe overlay. Does not delete files.
