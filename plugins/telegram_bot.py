"""
Telegram plugin shim for tests.

Provides a register() hook that schedules at least one job when a
TELEGRAM_TOKEN is configured.
"""
from __future__ import annotations

from typing import Callable, Iterable, Any


def _ping() -> str:
    """Very small job used only in tests."""
    return "ok"


def register(app, register_job: Callable[[str, Iterable[Callable[..., Any]]], None]) -> None:
    """Register Telegram jobs with the hosting app.

    Parameters
    ----------
    app:
        Object with a ``config`` mapping. Only the ``TELEGRAM_TOKEN``
        key is consulted here.
    register_job:
        Callback supplied by the caller; we invoke this with a
        plugin name and a non-empty list of jobs.
    """
    token = getattr(app, "config", {}).get("TELEGRAM_TOKEN")
    if not token:
        # If there's no token configured we simply don't register anything.
        return

    jobs = [_ping]
    register_job("telegram_bot", jobs=jobs)
