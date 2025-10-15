#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

echo "[cleanup] Scanning for placeholder migrations with revision=None..."
ROOT="$(dirname "$0")/.."
VER_DIR="$ROOT/migrations/versions"
FOUND=0
for f in "$VER_DIR"/*.py; do
  if grep -qE '^revision\s*=\s*None' "$f"; then
    echo "Deleting placeholder: $f"
    rm -f "$f"
    FOUND=$((FOUND+1))
  fi
done
if [ "$FOUND" -eq 0 ]; then
  echo "No placeholders found."
fi
