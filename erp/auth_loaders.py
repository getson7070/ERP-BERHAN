"""Module: auth_loaders.py — audit-added docstring. Refine with precise purpose when convenient."""
# erp/auth_loaders.py
from __future__ import annotations
from erp.extensions import load_user as canonical_load_user


def load_user(user_id: str):
    """
    Legacy shim that delegates to :func:`erp.extensions.load_user`.

    Keeping this function avoids breaking imports in older blueprints
    while ensuring a single policy enforcement point handles session
    principal restoration.
    """

    return canonical_load_user(user_id)



