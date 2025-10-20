#!/bin/bash
set -euo pipefail
HOST=${LOADTEST_HOST:-http://localhost:5000}
USERS=${USERS:-1000}
RATE=${RATE:-100}
DURATION=${DURATION:-5m}
if ! command -v locust >/dev/null; then
  echo "locust not installed" >&2
  exit 1
fi
locust -f "$(dirname "$0")/locustfile.py" --headless --host "$HOST" -u "$USERS" -r "$RATE" -t "$DURATION"
