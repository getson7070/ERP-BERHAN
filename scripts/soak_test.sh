#!/usr/bin/env bash
# Run a Locust soak test for two hours to validate stability
set -euo pipefail
locust -f scripts/locustfile.py --headless -u 100 -r 10 --run-time 2h
