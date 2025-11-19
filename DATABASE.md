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
- `scripts/pg_backup.sh` now writes custom-format dumps, SHA-256 manifests, and
  JSONL telemetry (`backup-report.jsonl`) so operators can attest to checksum
  integrity over time.【F:scripts/pg_backup.sh†L1-L62】
- When `pg_restore` is available, the script emits a manifest listing and schema
  reconstruction dry-run to catch corruption early without touching production
  data.【F:scripts/pg_backup.sh†L20-L42】
- The lightweight `python -m tools.backup_drill` wrapper is safe to run from laptops and CI runners
  so teams can verify credentials and binaries without invoking the heavier Bash pipeline.

## Normalization & Query Performance
- Adhere to third normal form (3NF) for transactional tables.
- Monitor query plans with `EXPLAIN ANALYZE` and review slow query logs.
- Update or archive obsolete indexes after audit to maintain write performance.
- WebAuthn credentials live in `webauthn_credentials` with a unique `credential_id` index and tenant-scoped RLS policy.

