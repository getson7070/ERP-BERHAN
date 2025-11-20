"""Helpers for client authentication flows (password hashing, verification)."""
from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash


def set_password(account, raw_password: str) -> None:
    account.password_hash = generate_password_hash(raw_password)


def verify_password(account, raw_password: str) -> bool:
    if not getattr(account, "password_hash", None):
        return False
    return check_password_hash(account.password_hash, raw_password)
