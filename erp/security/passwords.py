# erp/security/passwords.py

from __future__ import annotations

from werkzeug.security import generate_password_hash, check_password_hash

# IMPORTANT:
# pbkdf2:sha256 hashes are ~100 chars long, which fits safely in VARCHAR(128).
DEFAULT_PW_METHOD = "pbkdf2:sha256"
DEFAULT_PW_SALT_LENGTH = 16  # Werkzeug default, explicit for clarity.


def hash_password(plain_password: str) -> str:
    """
    Return a hashed password string suitable for storage in a VARCHAR(128) column.

    DO NOT store the plain password anywhere. Always store the return value of this.
    """
    if not plain_password:
        raise ValueError("Password cannot be empty")

    return generate_password_hash(
        plain_password,
        method=DEFAULT_PW_METHOD,
        salt_length=DEFAULT_PW_SALT_LENGTH,
    )


def verify_password(stored_hash: str, plain_password: str) -> bool:
    """
    Verify a plain password against a stored hash.

    Returns True if the password matches, False otherwise.
    """
    if not stored_hash or not plain_password:
        return False

    return check_password_hash(stored_hash, plain_password)
