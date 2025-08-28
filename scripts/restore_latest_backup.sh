#!/bin/bash
# Restore the most recent backup into the database defined by $DATABASE_URL.
set -euo pipefail
BACKUP_DIR=${BACKUP_DIR:-backups}
LATEST=$(ls -1t "$BACKUP_DIR"/*.sql 2>/dev/null | head -n1)
if [[ -z "${LATEST:-}" ]]; then
  echo "No backup files found in $BACKUP_DIR" >&2
  exit 1
fi
mkdir -p logs
start_ts=$(date -u +%s)
start_iso=$(date -u --iso-8601=seconds)
psql "${DATABASE_URL}" -f "$LATEST"
end_ts=$(date -u +%s)
end_iso=$(date -u --iso-8601=seconds)
rto=$((end_ts - start_ts))
backup_ts=$(stat -c %Y "$LATEST")
rpo=$((start_ts - backup_ts))
echo "$start_iso,$end_iso,$rpo,$rto,$LATEST" >> logs/restore_drill.log
