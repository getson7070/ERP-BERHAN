#!/bin/bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL not set}"

BACKUP_DIR=${BACKUP_DIR:-backups}
REPORT_PATH=${BACKUP_REPORT_PATH:-$BACKUP_DIR/backup-report.jsonl}
mkdir -p "$BACKUP_DIR"

STAMP=$(date +%Y%m%d%H%M%S)
FILE="$BACKUP_DIR/erp-${STAMP}.dump"

pg_dump --format=custom --blobs "$DATABASE_URL" > "$FILE"

read -r SHA _ < <(sha256sum "$FILE")
printf "%s  %s\n" "$SHA" "$FILE" > "$FILE.sha256"

MANIFEST=""
MANIFEST_COUNT=0
if command -v pg_restore >/dev/null 2>&1; then
  MANIFEST="$FILE.manifest"
  pg_restore --list "$FILE" > "$MANIFEST"
  MANIFEST_COUNT=$(wc -l < "$MANIFEST" | tr -d ' ')
  pg_restore --schema-only --file=/dev/null "$FILE" >/dev/null
fi

python <<PY
import json
import os
import time

file_path = "$FILE"
sha = "$SHA"
manifest = "$MANIFEST"
manifest_count = $MANIFEST_COUNT
report_path = "$REPORT_PATH"
directory = os.path.dirname(report_path) or "."
os.makedirs(directory, exist_ok=True)

entry = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "file": os.path.basename(file_path),
    "sha256": sha,
    "size_bytes": os.path.getsize(file_path),
}

if manifest:
    entry["manifest"] = os.path.basename(manifest)
    entry["manifest_entries"] = manifest_count

with open(report_path, "a", encoding="utf-8") as fh:
    json.dump(entry, fh)
    fh.write("\n")

print(f"wrote {file_path}")
print(f"sha256 {sha}")
if manifest:
    print(f"manifest entries: {manifest_count}")
print(f"report appended to {report_path}")
PY
