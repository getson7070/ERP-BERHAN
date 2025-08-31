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

if ! command -v pip-audit >/dev/null 2>&1; then
  echo "pip-audit is required for dependency checks" >&2
  exit 1
fi

# Static analysis for common Python security issues
bandit -r erp

# Dependency vulnerability audit
if [[ -f requirements.txt ]]; then
    pip-audit -r requirements.txt
else
    pip-audit
fi
