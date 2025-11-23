"""Backwards-compatible import for the performance review model.

The authoritative model now lives in :mod:`erp.models.hr_lifecycle` to keep
all HR lifecycle entities together. Existing imports that point here continue
working by re-exporting the same class.
"""

from __future__ import annotations

from erp.models.hr_lifecycle import PerformanceReview  # noqa: F401

__all__ = ["PerformanceReview"]
