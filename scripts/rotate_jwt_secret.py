#!/usr/bin/env python3
"""Rotate JWT secrets using KID playbook with audit logging."""
import datetime
import json
import os
import pathlib
import secrets

SECRETS_FILE = pathlib.Path("jwt_secrets.json")
LOG_FILE = pathlib.Path("logs/jwt_rotation.log")


def load_secrets() -> dict:
    if SECRETS_FILE.exists():
        return json.loads(SECRETS_FILE.read_text())
    return json.loads(os.environ.get('JWT_SECRETS', '{}'))


def save_secrets(data: dict) -> None:
    SECRETS_FILE.write_text(json.dumps(data))
    os.environ['JWT_SECRETS'] = json.dumps(data)


def log_rotation(kid: str) -> None:
    LOG_FILE.parent.mkdir(exist_ok=True)
    with LOG_FILE.open('a') as fh:
        fh.write(
            f"{datetime.datetime.utcnow().isoformat()} rotated to {kid}\n"
        )


secrets_map = load_secrets()
new_id = f"v{len(secrets_map)+1}"
secrets_map[new_id] = secrets.token_hex(32)
save_secrets(secrets_map)
os.environ['JWT_SECRET_ID'] = new_id
log_rotation(new_id)
print(f"Rotated to {new_id}")
