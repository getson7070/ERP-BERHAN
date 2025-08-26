#!/bin/bash
set -euo pipefail
# Simple load test using wrk if available
if ! command -v wrk >/dev/null; then
  echo "wrk not installed" >&2
  exit 1
fi
wrk -t4 -c100 -d30s http://localhost:5000/
