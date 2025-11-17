"""Deprecated finance package.

The finance API has been consolidated in ``erp/routes/finance.py``.  This
package re‑exports the blueprint defined there for backward compatibility with
existing imports.
"""

from __future__ import annotations

from erp.routes.finance import bp  # noqa: F401

__all__ = ["bp"]
