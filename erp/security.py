"""Encryption utilities for protecting sensitive data.

This module provides helpers backed by :class:`cryptography.fernet.Fernet` to
encrypt or decrypt payloads such as API tokens.  For guidelines on access
recertification and periodic reviews see ``docs/access_recerts.md``.
"""

from __future__ import annotations

import os
from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    """Return a Fernet instance configured from ``FERNET_KEY``.

    A random key is generated the first time if the environment variable is not
    set, allowing the application to operate in development environments while
    encouraging explicit key management in production.
    """

    key = os.environ.get("FERNET_KEY")
    key_bytes = key.encode() if key else Fernet.generate_key()
    return Fernet(key_bytes)


def encrypt(value: str) -> str:
    """Encrypt *value* using Fernet."""

    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt *token* using Fernet."""

    return _get_fernet().decrypt(token.encode()).decode()
