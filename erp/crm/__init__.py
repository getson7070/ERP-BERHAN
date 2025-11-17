"""Backwards‑compatible CRM package.

Historically the CRM module exposed its own models and blueprint in
``erp/crm/routes.py`` and ``erp/crm/models.py``.  Those modules are now
deprecated in favour of the consolidated blueprint and models in
``erp/routes/crm.py`` and ``erp/models/core_entities.py``.

This package re‑exports the new blueprint as ``bp`` and the core models
for code that still imports from ``erp.crm``.  Applications should
eventually import from ``erp.routes.crm`` and ``erp.models`` directly.
"""

from __future__ import annotations

from erp.routes.crm import bp  # noqa: F401
from erp.models import CrmLead as Lead, CrmInteraction as Interaction  # noqa: F401

__all__ = ["bp", "Lead", "Interaction"]
