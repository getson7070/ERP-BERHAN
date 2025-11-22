# Audit Trail & Immutable Logging

This document outlines the audit spine added for compliance and forensics.

## Data model
- **AuditLog** (append-only) with:
  - actor_type/actor_id, module, action, severity
  - entity_type/entity_id for quick scoping
  - searchable `metadata_json` and encrypted `payload_encrypted`
  - legacy hash-chain fields (`prev_hash`/`hash`) retained for tamper evidence

## Security controls
- Database trigger blocks UPDATE/DELETE on `audit_logs` (append-only).
- Sensitive fields encrypted via Fernet (`AUDIT_FERNET_KEY` config).
- Search filters operate only on metadata and headers; decrypted payloads require admin/compliance roles.

## API endpoints
- `GET /api/audit/logs` — cursor-paginated search with filters.
- `GET /api/audit/logs/<id>` — fetch a single entry (payload only for admin/compliance).
- `POST /api/audit/export` — export up to 5k rows for investigations.

## Operations
- Celery task `erp.tasks.audit.retention_sweep` returns counts (or deletes if `hard_delete=True`).
- Configure `AUDIT_FERNET_KEY` (base64 URL-safe 32-byte) in env; dev falls back to a key derived from `SECRET_KEY`.

## Integration tips
- Use `write_audit_log()` for new flows; legacy `log_audit()` remains compatible.
- Store only non-PII in `metadata_json`; encrypt PII via `payload_encrypted`.
- Always scope by `resolve_org_id()` to maintain tenant isolation.
