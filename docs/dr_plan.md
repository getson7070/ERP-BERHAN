# Disaster Recovery Plan

This document outlines recovery objectives and drill procedures.

## Objectives
- **Recovery Point Objective (RPO):** 15 minutes
- **Recovery Time Objective (RTO):** 1 hour

## Backup Strategy
- Nightly readiness checks use `python -m tools.backup_drill --database-url=$DATABASE_URL` to
  exercise `pg_dump`/`pg_restore` and emit a manifest in `logs/backup-drill/` for audit evidence.
- Production backups should be captured by your managed database service or infrastructure pipeline;
  replicate off‑site (e.g., S3) with a 30‑day retention policy.

## Restore Drill
Monthly restore drills validate the latest managed backup on a staging database.
Use the backup drill manifest to confirm tooling works before restoring a
production snapshot.

1. Provision a staging database and set `DATABASE_URL` (include `?sslmode=require`).
2. Run a readiness check if `pg_dump`/`pg_restore` paths changed:
   ```bash
   python -m tools.backup_drill --database-url=$DATABASE_URL --output-dir=logs/backup-drill
   ```
3. Restore the latest managed backup into staging and measure start/end times to confirm the
   **RTO ≤ 1 hour**.
4. Compare the backup timestamp against the drill time to validate the **RPO ≤ 15 minutes**.
5. Verify application health checks and record completion time.

Each log entry follows:

```
start_iso,end_iso,rpo_seconds,rto_seconds,backup_file
```

Results of each drill are reviewed monthly to ensure the measured RPO/RTO
values remain within objectives.
