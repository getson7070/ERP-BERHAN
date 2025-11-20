# Banking Integration & Cashflow

This document outlines the banking integration scaffolding built on top of the finance GL and reconciliation layers.

## 1. Data Model Highlights

- **BankAccount** – maps physical accounts to GL codes, tracks currency, masking, default status, and activation.
- **BankConnection** – API configuration per bank/provider (sandbox vs live), optional two-factor metadata.
- **BankAccessToken** – stores access/refresh tokens (encrypt or store in a vault in production).
- **BankTwoFactorChallenge** – records OTP/push challenges without persisting secrets.
- **BankSyncJob** – audit-friendly tracker for each statement sync, including counts and errors.

## 2. API Endpoints (`/api/banking`)

- `GET/POST /accounts` – manage bank accounts bound to GL codes.
- `GET/POST /connections` – configure bank API endpoints and credentials metadata.
- `POST /connections/<id>/tokens` – save tokens from OAuth/2FA flows (logs to `FinanceAuditLog`).
- `POST /connections/<id>/2fa/challenge` – record a 2FA request; `POST /verify` marks success/failure.
- `POST /connections/<id>/sync` – create a sync job and dispatch Celery task (synchronous fallback in dev/test).
- `GET /sync-jobs` – list recent jobs with status and counts.
- `GET /cashflow` – 60-day history (default) and 30-day forecast using bank statement lines.

## 3. Celery Task

- `erp.tasks.bank_sync.run_sync_job(job_id)`
  - Loads the latest token, fetches statement rows via provider adapters (stubbed for now).
  - Writes a `BankStatement` + `BankStatementLine` entries and updates `BankSyncJob`.
  - Emits `FinanceAuditLog` events for both success and failure.

## 4. Security & Compliance Notes

- Tokens and credentials must be encrypted or stored in an external vault.
- No OTP values are ever stored; only challenge metadata and status are persisted.
- All operations are tenant-scoped via `resolve_org_id()` and guarded by `@require_roles("finance", "admin")`.
- Audit logs capture token updates, 2FA verifications, and sync job creation/results.

## 5. Next Steps

- Implement provider adapters in `_fetch_statements_from_api` for CBE/Awash/etc.
- Extend cashflow endpoint with currency/account filters and richer forecasting.
- Add integration tests that mock provider HTTP calls and validate job lifecycle transitions.
