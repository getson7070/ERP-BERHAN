#!/bin/bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL not set}"
BACKUP_DIR=${BACKUP_DIR:-backups}
mkdir -p "$BACKUP_DIR"
FILE="$BACKUP_DIR/erp-$(date +%Y%m%d%H%M).sql.gz"
pg_dump "$DATABASE_URL" | gzip > "$FILE"
sha256sum "$FILE" > "$FILE.sha256"
echo "wrote $FILE"
