"""Encryption utilities for protecting sensitive data.

This module provides helpers backed by :class:`cryptography.fernet.Fernet` to
encrypt or decrypt payloads such as API tokens.  For guidelines on access
recertification and periodic reviews see ``docs/access_recerts.md``.
"""

from __future__ import annotations

from cryptography.fernet import Fernet

from .secrets import get_secret


def _get_fernet() -> Fernet:
    """Return a Fernet instance configured from ``FERNET_KEY``.

    The key must be supplied via the environment or secret store.  A missing
    key indicates misconfiguration and will abort application start-up instead
    of generating an ephemeral key that would break cross-process decryption.
    """

    key = get_secret("FERNET_KEY")
    if not key:
        raise RuntimeError("FERNET_KEY is required")
    return Fernet(key.encode())


def encrypt(value: str) -> str:
    """Encrypt *value* using Fernet."""

    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt *token* using Fernet."""

    return _get_fernet().decrypt(token.encode()).decode()
