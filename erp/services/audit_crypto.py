"""Encryption helpers for audit payloads."""
from __future__ import annotations

from cryptography.fernet import Fernet
from flask import current_app, has_app_context


def _fernet() -> Fernet:
    if not has_app_context():
        raise RuntimeError("AUDIT_FERNET_KEY requires an application context")
    key = current_app.config.get("AUDIT_FERNET_KEY")
    if not key:
        raise RuntimeError("AUDIT_FERNET_KEY not configured; set it in the environment")
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_value(value) -> str:
    """Encrypt a single scalar value using Fernet."""
    token = _fernet().encrypt(str(value).encode("utf-8"))
    return token.decode("utf-8")


def decrypt_value(token: str):
    """Decrypt a previously encrypted value."""
    return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")


def encrypt_payload(payload: dict, sensitive_keys: set[str]) -> dict:
    """Encrypt only the sensitive keys from *payload*.

    Non-sensitive values should be placed in ``metadata_json`` to remain
    searchable; encrypted values are stored separately to protect PII.
    """
    if not payload:
        return {}

    encrypted: dict[str, str] = {}
    for key, value in payload.items():
        if key in sensitive_keys and value is not None:
            encrypted[key] = encrypt_value(value)
    return encrypted


def decrypt_payload(enc_payload: dict | None) -> dict:
    if not enc_payload:
        return {}
    return {key: decrypt_value(val) for key, val in enc_payload.items()}
