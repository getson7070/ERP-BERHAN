import os
import sys
from pathlib import Path

# Ensure the repository root is importable so tests can locate the `erp` package
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Use in-memory Redis and dummy secrets for test runs to avoid external dependencies
os.environ.setdefault("USE_FAKE_REDIS", "1")
os.environ.setdefault("SECURITY_PASSWORD_SALT", "test-salt")
os.environ.setdefault("JWT_SECRET", "test-secret")
