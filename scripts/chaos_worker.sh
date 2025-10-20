#!/usr/bin/env bash
# Simulate worker failure for chaos testing
set -euo pipefail
pid=$(pgrep -f 'celery worker' || true)
if [[ -n "$pid" ]]; then
  kill -9 "$pid"
  echo "Killed Celery worker $pid"
else
  echo "No Celery worker running"
fi
