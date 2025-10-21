import json
import os
from threading import RLock
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

_cache: dict[str, Any] = {}
_lock = RLock()


def get_secret(key: str) -> str | None:
    """Return secret value from a vault file, env var, or AWS Secrets Manager.

    The vault file path is supplied via the ``VAULT_FILE`` environment variable.
    Secrets are reloaded automatically if the file changes to support rotation
    without restarting the application.  If a secret is not found in the vault
    or environment, ``AWS_SECRETS_PREFIX`` is used to look up the value from
    AWS Secrets Manager.
    """
    path = os.environ.get("VAULT_FILE")
    if not path:
        env_val = os.environ.get(key)
        if env_val:
            return env_val
    else:
        with _lock:
            mtime = os.path.getmtime(path)
            if _cache.get("_mtime") != mtime:
                with open(path) as fh:
                    _cache.clear()
                    _cache.update(json.load(fh))
                    _cache["_mtime"] = mtime
            if key in _cache:
                return _cache[key]
            env_val = os.environ.get(key)
            if env_val:
                return env_val

    prefix = os.environ.get("AWS_SECRETS_PREFIX")
    if not prefix:
        return None
    secret_name = f"{prefix}{key}"
    cache_key = f"aws:{secret_name}"
    with _lock:
        if cache_key in _cache:
            return _cache[cache_key]
    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)
        secret_val = response.get("SecretString")
    except (BotoCoreError, ClientError):
        return None
    with _lock:
        _cache[cache_key] = secret_val
    return secret_val


