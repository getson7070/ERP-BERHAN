#!/bin/bash
# Restore the most recent backup into the database defined by $DATABASE_URL.
set -euo pipefail
BACKUP_DIR=${BACKUP_DIR:-backups}
LATEST=$(ls -1t "$BACKUP_DIR"/*.sql 2>/dev/null | head -n1)
if [[ -z "${LATEST:-}" ]]; then
  echo "No backup files found in $BACKUP_DIR" >&2
  exit 1
fi
psql "${DATABASE_URL}" -f "$LATEST"
mkdir -p logs
echo "$(date -u) restored $LATEST" >> logs/restore_drill.log
