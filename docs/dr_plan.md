# Disaster Recovery Plan

This document outlines recovery objectives and drill procedures.

## Objectives
- **Recovery Point Objective (RPO):** 15 minutes
- **Recovery Time Objective (RTO):** 1 hour

## Backup Strategy
- Nightly `pg_dump` stored in `backups/` with encryption.
- Off‑site copies replicated to S3 with 30‑day retention.

## Restore Drill
Nightly backups and monthly restore drills are automated via Celery beat
(`backup.run_backup` and `backup.run_restore_drill`). The latest dump is restored
into a staging database and results are logged to `logs/restore_drill.log`.

1. Provision a staging database and set `DATABASE_URL` (include `?sslmode=require`).
2. Execute the script manually if needed:
   ```bash
   python scripts/dr_drill.py
   ```
3. Measure start and end times to confirm the **RTO ≤ 1 hour**.
4. Compare the backup timestamp against the drill time to validate the
   **RPO ≤ 15 minutes**.
5. Verify application health checks and record completion time.

Each log entry follows:

```
start_iso,end_iso,rpo_seconds,rto_seconds,backup_file
```

Results of each drill are reviewed monthly to ensure the measured RPO/RTO
values remain within objectives.
