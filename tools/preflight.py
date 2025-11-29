"""
Pre-flight environment sanity check for deployments.

Fail fast if critical env vars are missing so we do not start a half-configured app.
"""

import os
import sys

REQUIRED_VARS = [
    "DATABASE_URL",
    "SECRET_KEY",
]


def main() -> int:
    missing = [name for name in REQUIRED_VARS if not os.getenv(name)]
    if missing:
        print(f"Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
