"""
Simple secret rotation utility used by tests.

The tests expect:
- A module-level SECRETS_FILE and LOG_FILE Path.
- A main() function that:
  * writes a JSON file with DB_PASSWORD and API_KEY keys,
  * each value exactly 32 characters long,
  * writes a non-empty rotation log line,
  * returns the secrets dict.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Dict

# Default locations (tests monkeypatch these to a tmp_path)
SECRETS_FILE: Path = Path("secrets.json")
LOG_FILE: Path = Path("secrets-rotation.log")


def _generate_secret() -> str:
    """Generate a 32-character secret string.

    We use token_hex(16) => 16 bytes => 32 hex characters.
    This matches tests that assert len(secret) == 32.
    """
    return secrets.token_hex(16)


def main() -> Dict[str, str]:
    """Rotate secrets and persist them to disk.

    Returns the new secrets dict so tests can make assertions.
    """
    secrets_dict: Dict[str, str] = {
        "DB_PASSWORD": _generate_secret(),
        "API_KEY": _generate_secret(),
    }

    # Write secrets JSON
    SECRETS_FILE.write_text(
        json.dumps(secrets_dict, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # Append a simple rotation log line
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_line = f"{timestamp} rotated DB_PASSWORD and API_KEY\n"
    LOG_FILE.write_text(log_line, encoding="utf-8")

    return secrets_dict


if __name__ == "__main__":
    main()
