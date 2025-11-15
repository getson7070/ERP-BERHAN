# -*- coding: utf-8 -*-
"""
Centralized secret accessor. Sources:
1) Environment variables
2) AWS Secrets Manager (optional, if configured)
No literal defaults here.
"""
from __future__ import annotations
import os
from threading import RLock
from typing import Any, Optional

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    boto3 = None
    BotoCoreError = ClientError = Exception

_cache: dict[str, Any] = {}
_lock = RLock()
AWS_SECRET_PREFIX = os.getenv("AWS_SECRET_PREFIX", "").rstrip("/")  # e.g. "prod/erp"

def _aws_get(name: str) -> Optional[str]:
    if not boto3 or not AWS_SECRET_PREFIX:
        return None
    try:
        client = boto3.client("secretsmanager")
        full = f"{AWS_SECRET_PREFIX}/{name}"
        resp = client.get_secret_value(SecretId=full)
        return resp.get("SecretString")
    except (BotoCoreError, ClientError):
        return None

def get_secret(name: str) -> Optional[str]:
    with _lock:
        if name in _cache:
            return _cache[name]
        val = os.getenv(name)
        if val:
            _cache[name] = val
            return val
        val = _aws_get(name)
        if val:
            _cache[name] = val
            return val
        return None