#!/usr/bin/env python3
"""Utility for generating cryptographically strong Flask secret keys."""

from __future__ import annotations

import argparse
import secrets
from typing import Iterable

DEFAULT_TOKEN_BYTES = 64


def _generate_token(bytes_length: int) -> str:
    return secrets.token_urlsafe(bytes_length)


def _emit(name: str, token: str) -> str:
    return f"{name}={token}"


def generate_keys(bytes_length: int) -> Iterable[str]:
    yield _emit("FLASK_SECRET_KEY", _generate_token(bytes_length))
    yield _emit("WTF_CSRF_SECRET_KEY", _generate_token(bytes_length))
    yield _emit("SECURITY_PASSWORD_SALT", _generate_token(bytes_length))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate secure secrets for Flask and Flask-WTF configuration.",
    )
    parser.add_argument(
        "--bytes",
        type=int,
        default=DEFAULT_TOKEN_BYTES,
        help="Number of random bytes to use per secret before url-safe encoding (default: %(default)s).",
    )
    args = parser.parse_args()

    for line in generate_keys(args.bytes):
        print(line)


if __name__ == "__main__":
    main()


