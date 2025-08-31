#!/usr/bin/env python3
"""Rotate database and API secrets with audit logging."""

import datetime
import json
import os
import pathlib
import secrets
from typing import Dict

SECRETS_FILE = pathlib.Path("secrets.json")
LOG_FILE = pathlib.Path("logs/secret_rotation.log")


def rotate_secret(name: str) -> str:
    token = secrets.token_hex(16)
    os.environ[name] = token
    return token


def main() -> Dict[str, str]:
    secrets_map = {
        "DB_PASSWORD": rotate_secret("DB_PASSWORD"),
        "API_KEY": rotate_secret("API_KEY"),
    }
    SECRETS_FILE.write_text(json.dumps(secrets_map))
    LOG_FILE.parent.mkdir(exist_ok=True)
    with LOG_FILE.open("a") as fh:
        fh.write(
            f"{datetime.datetime.utcnow().isoformat()} rotated {','.join(secrets_map)}\n"
        )
    print("Rotated secrets:", ",".join(secrets_map))
    return secrets_map


if __name__ == "__main__":
    main()
