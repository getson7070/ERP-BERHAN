"""Backwards‑compatible CRM models.

This module re‑exports the models defined in ``erp/models/core_entities.py`` for
historical compatibility.  New code should import from ``erp.models`` or
``erp.models.core_entities`` directly.
"""

from __future__ import annotations

from erp.models import CrmLead as Lead, CrmInteraction as Interaction  # noqa: F401
from erp.models import SalesOpportunity  # noqa: F401

__all__ = ["Lead", "Interaction", "SalesOpportunity"]
