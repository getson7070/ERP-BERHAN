"""
Root-level plugins compatibility shim.

The real implementations live under :mod:`erp.plugins`, but the test
suite imports them as::

    from plugins import telegram_bot

This package simply re-exports the public plugin modules from
``erp.plugins`` so those imports continue to work.
"""
from __future__ import annotations

from erp.plugins import telegram_bot  # type: ignore[attr-defined]

__all__ = ["telegram_bot"]
