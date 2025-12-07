"""Module: auth/user_loader.py — audit-added docstring. Refine with precise purpose when convenient."""
from ..extensions import load_user as canonical_load_user


def load_user(user_id: str):
    """Legacy shim delegating to :func:`erp.extensions.load_user`."""

    return canonical_load_user(user_id)



