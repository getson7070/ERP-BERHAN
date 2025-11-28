# Database Operations

This document records database maintenance practices.

## Index Auditing
- Run `python -m tools.index_audit` in CI and before major releases. The helper connects to the
  configured `DATABASE_URL`, asserts the presence of critical indexes (audit log, finance ledgers,
  and order workflows), and fails with actionable remediation guidance if anything is missing.
- Investigate any table reporting sequential scans without index usage and create indexes accordingly.

## RPO/RTO Targets
- **Recovery Point Objective (RPO):** ≤15 minutes
- **Recovery Time Objective (RTO):** ≤60 minutes
- Monthly restore drills via `python -m tools.backup_drill` verify these objectives. The script runs a
  schema-only `pg_dump` against the production database, verifies `pg_restore --list` succeeds, and
  captures the manifest in `logs/backup-drill/` for auditor review.

## Backups
- `python -m tools.backup_drill` is the supported backup drill for this codebase. It issues a
  schema-only `pg_dump --format=custom`, confirms `pg_restore --list` can read the archive, and
  writes the manifest to `logs/backup-drill/` so operators can attest to checksum integrity over
  time.【F:tools/backup_drill.py†L1-L53】
- Example (safe for laptops and CI runners):
  ```bash
  python -m tools.backup_drill --database-url=$DATABASE_URL --output-dir=logs/backup-drill
  ```
- Pair the drill with monthly restore validations on staging databases to prove RPO/RTO readiness
  and capture artifacts for auditors.

## Automated Resilience Suite
- Run `python -m tools.run_resilience_suite --database-url=$DATABASE_URL` nightly. The helper chains the
  backup drill and index audit, persists JSON evidence under `logs/resilience-suite/`, and fails the
  job if either step returns a non-zero status.
- Attach the resulting JSON artifact to change-management tickets so auditors can verify recovery
  readiness without re-running the scripts.

## Tenant Isolation Guardrails
- Every Flask request now flows through `erp.middleware.tenant_guard.install_tenant_guard`, which
  resolves `org_id` from headers, query parameters, or the authenticated user. Requests that omit an
  organisation id are rejected with `400 org_id_required` whenever `STRICT_ORG_BOUNDARIES=1`.
- Application code should continue calling `resolve_org_id()`—it now honours the pre-populated `g.org_id`
  and falls back to the configured `DEFAULT_ORG_ID` only during local or automated tests.

## Normalization & Query Performance
- Adhere to third normal form (3NF) for transactional tables.
- Monitor query plans with `EXPLAIN ANALYZE` and review slow query logs.
- Update or archive obsolete indexes after audit to maintain write performance.
- WebAuthn credentials live in `webauthn_credentials` with a unique `credential_id` index and tenant-scoped RLS policy.

