import os

# Use in-memory Redis and dummy secrets for test runs to avoid external dependencies
os.environ.setdefault("USE_FAKE_REDIS", "1")
os.environ.setdefault("SECURITY_PASSWORD_SALT", "test-salt")
os.environ.setdefault("JWT_SECRET", "test-secret")
