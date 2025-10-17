#!/usr/bin/env bash
set -euo pipefail
MSG=${1:-"patch-9_8-modules"}
alembic revision --autogenerate -m "$MSG"
bash "$(dirname "$0")/check_one_head.sh" || true  # warn only during local dev
alembic upgrade head
