# Backup & Restore

## Backups
- Daily: `pg_dump` (sanitized copy kept for smoke tests)
- Weekly: full dump to secure storage
- Retention: 30 daily / 12 weekly / 12 monthly

## Restore Drill (monthly)
1. Create temp DB: `erp_restore_drill`
2. Restore latest dump
3. Run `tools/migrations_smoke.py`
4. Run smoke tests
5. Record outcome

## Disaster Restore
1. Freeze writes
2. Restore to new DB
3. Point app `DATABASE_URL` to new DB
4. Verify `/readyz` and critical flows
