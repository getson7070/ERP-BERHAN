"""
Simple secrets rotation utility used by tests.

In real deployments, hook this into your secret backend instead of
writing to local JSON files.
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from datetime import datetime

# These are patched by tests to point into a tmp directory, so we keep
# them as module-level variables – don't inline in main().
SECRETS_FILE = Path("secrets.json")
LOG_FILE = Path("secrets-rotation.log")


def _generate_secret() -> str:
    return secrets.token_urlsafe(32)


def main() -> dict[str, str]:
    """Rotate DB and API secrets and log the operation."""
    new_secrets = {
        "DB_PASSWORD": _generate_secret(),
        "API_KEY": _generate_secret(),
    }

    # Write JSON atomically
    SECRETS_FILE.write_text(json.dumps(new_secrets), encoding="utf-8")

    # Very small log line – tests only check that it's non-empty
    timestamp = datetime.utcnow().isoformat() + "Z"
    LOG_FILE.write_text(
        f"{timestamp} rotated DB_PASSWORD and API_KEY\n",
        encoding="utf-8",
    )

    return new_secrets


if __name__ == "__main__":  # pragma: no cover - manual runs only
    main()