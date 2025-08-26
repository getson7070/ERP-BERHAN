#!/bin/bash
set -euo pipefail
bandit -r erp
safety check || true
