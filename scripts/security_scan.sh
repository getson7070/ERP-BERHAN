#!/bin/bash
#
# Run static and dependency security checks. Fails if issues are detected.
# Usage: ./scripts/security_scan.sh
set -euo pipefail

# Ensure required tools are available
if ! command -v bandit >/dev/null 2>&1; then
  echo "Bandit is required for static analysis" >&2
  exit 1
fi

if ! command -v safety >/dev/null 2>&1; then
  echo "Safety is required for dependency checks" >&2
  exit 1
fi

# Static analysis for common Python security issues
bandit -r erp

# Dependency vulnerability audit
if [[ -f requirements.txt ]]; then
    safety check -r requirements.txt --full-report
else
    safety check --full-report
fi
