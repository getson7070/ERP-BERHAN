# Online Migration Guidelines

1. **Add nullable column** with default.
2. **Backfill in batches** using Celery task or script.
3. **Add constraints** (not null / foreign keys).
4. **Drop old columns** only after verifying application compatibility.

Use the pattern `add-nullable → backfill → enforce-not-null` to avoid locks. Run migrations in off-peak hours and monitor metrics.
