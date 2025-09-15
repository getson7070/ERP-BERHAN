# Database Operations

This document records database maintenance practices.

## Index Auditing
- Run `scripts/index_audit.py` in CI and before major releases.
- Investigate any table reporting sequential scans without index usage and create indexes accordingly.

## RPO/RTO Targets
- **Recovery Point Objective (RPO):** ≤15 minutes
- **Recovery Time Objective (RTO):** ≤60 minutes
- Monthly restore drills via `scripts/dr_drill.sh` verify these objectives.

## Normalization & Query Performance
- Adhere to third normal form (3NF) for transactional tables.
- Monitor query plans with `EXPLAIN ANALYZE` and review slow query logs.
- Update or archive obsolete indexes after audit to maintain write performance.
- WebAuthn credentials live in `webauthn_credentials` with a unique `credential_id` index and tenant-scoped RLS policy.

