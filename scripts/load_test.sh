#!/bin/bash
set -euo pipefail
HOST=${LOADTEST_HOST:-http://localhost:5000}
if ! command -v locust >/dev/null; then
  echo "locust not installed" >&2
  exit 1
fi
locust -f "$(dirname "$0")/locustfile.py" --headless --host "$HOST" -u 100 -r 20 -t 1m
