"""Encryption utilities for protecting sensitive data.

These helpers rely on Fernet symmetric encryption.  Rotate keys regularly and
consult ``docs/access_recerts.md`` for guidance on periodic access reviews.
"""
from __future__ import annotations

from cryptography.fernet import Fernet


def generate_key() -> bytes:
    """Return a new base64-encoded key suitable for :class:`Fernet`."""
    return Fernet.generate_key()


def encrypt(data: bytes, key: bytes) -> bytes:
    """Encrypt *data* using *key*."""
    return Fernet(key).encrypt(data)


def decrypt(token: bytes, key: bytes) -> bytes:
    """Decrypt *token* using *key*."""
    return Fernet(key).decrypt(token)
