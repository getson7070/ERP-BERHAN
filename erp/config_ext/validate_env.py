import os, sys
from typing import Iterable

REQUIRED_ENV_DEFAULT = [
    "SECRET_KEY",
    "DATABASE_URL",
    "REDIS_URL",
]

def validate_required_env(required: Iterable[str]) -> None:
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        sys.stderr.write(f"[ENV] Missing required variables: {', '.join(missing)}\n")
        sys.exit(1)
