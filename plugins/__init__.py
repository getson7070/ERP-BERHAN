"""
Root-level plugins compatibility shim for tests.

The real Telegram plugin implementation lives under :mod:`erp.plugins`.
The test suite imports it as::

    from plugins import telegram_bot

This package re-exports the ``telegram_bot`` module from the actual
implementation so those imports work.
"""
from __future__ import annotations

# Import the actual implementation
from erp.plugins import telegram_bot as _telegram_bot  # type: ignore[attr-defined]

# Expose it under the expected name
telegram_bot = _telegram_bot

__all__ = ["telegram_bot"]
