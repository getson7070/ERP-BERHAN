"""Deprecated finance approval routes.

The approval functionality is integrated into the main finance blueprint.
This module remains for backwards compatibility and re‑exports the finance
blueprint from ``erp/routes/finance.py``.
"""

from __future__ import annotations

from erp.routes.finance import bp  # noqa: F401

__all__ = ["bp"]
