# Disaster Recovery Plan

This document outlines recovery objectives and drill procedures.

## Objectives
- **Recovery Point Objective (RPO):** 15 minutes
- **Recovery Time Objective (RTO):** 1 hour

## Backup Strategy
- Nightly `pg_dump` stored in `backups/` with encryption.
- Off‑site copies replicated to S3 with 30‑day retention.

## Restore Drill
Run `scripts/restore_latest_backup.sh` weekly. The script restores the most
recent dump into a staging database and logs the result to `logs/restore_drill.log`.

1. Provision a staging database and set `DATABASE_URL`.
2. Execute the script:
   ```bash
   ./scripts/restore_latest_backup.sh
   ```
3. Measure start and end times to confirm the **RTO ≤ 1 hour**.
4. Compare the backup timestamp against the drill time to validate the
   **RPO ≤ 15 minutes**.
5. Verify application health checks and record completion time.

Results of each drill are reviewed and the measured RPO/RTO values are logged
to ensure objectives remain achievable.
