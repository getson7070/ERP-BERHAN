"""HR models shim to reuse canonical models without duplicate tables."""

from __future__ import annotations

from erp.models.recruitment import Recruitment  # noqa: F401
from erp.models.hr_lifecycle import PerformanceReview  # noqa: F401

__all__ = ["Recruitment", "PerformanceReview"]
