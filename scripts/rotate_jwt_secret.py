#!/usr/bin/env python3
"""Rotate JWT secrets using KID playbook."""
import json, os, secrets

secrets_map = json.loads(os.environ.get('JWT_SECRETS', '{}'))
new_id = f"v{len(secrets_map)+1}"
secrets_map[new_id] = secrets.token_hex(32)
os.environ['JWT_SECRETS'] = json.dumps(secrets_map)
os.environ['JWT_SECRET_ID'] = new_id
print(f"Rotated to {new_id}")
