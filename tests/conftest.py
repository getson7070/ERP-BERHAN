import os
import sys

# Ensure the repository root is importable for tests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Use in-memory Redis and dummy secrets for test runs to avoid external dependencies
os.environ.setdefault("USE_FAKE_REDIS", "1")
os.environ.setdefault("SECURITY_PASSWORD_SALT", "test-salt")
os.environ.setdefault("JWT_SECRET", "test-secret")
