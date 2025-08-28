# Online Migration Guidelines

Follow this playbook to apply schema changes without downtime:

1. **Expand** – Add nullable columns or new tables with defaults that keep
   existing queries functional.
2. **Backfill** – Populate new structures in small batches via a Celery task or
   one-off script. Track progress and pause on errors.
3. **Verify** – Deploy application code that reads from both old and new
   fields. Run canary instances and monitor metrics and logs.
4. **Contract** – Enforce `NOT NULL` or foreign-key constraints once the
   backfill is complete, then drop legacy columns.

Use the pattern `expand → backfill → verify → contract` to avoid locks. Run
migrations in off‑peak hours, emit metrics around migration duration, and
document rollback steps for each stage.
