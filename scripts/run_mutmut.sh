#!/usr/bin/env bash
set -euo pipefail
mutmut run --paths erp --tests-dir tests --runner pytest
mutmut results --show-mutant 0 --exit-code
