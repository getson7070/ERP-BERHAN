import os

# Use in-memory Redis for test runs to avoid external dependencies
os.environ.setdefault("USE_FAKE_REDIS", "1")
