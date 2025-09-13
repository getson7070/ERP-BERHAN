#!/bin/bash
set -euo pipefail
BASE_URL=${1:-http://localhost:5000}
pa11y-ci "$BASE_URL" "$BASE_URL/login" "$BASE_URL/dashboard" --json > pa11y-report.json
