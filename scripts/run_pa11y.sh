#!/usr/bin/env bash
set -euo pipefail

URLS=(
  "http://localhost:5000/"
  "http://localhost:5000/login"
  "http://localhost:5000/dashboard"
)

for url in "${URLS[@]}"; do
  pa11y "$url" --reporter cli
done
