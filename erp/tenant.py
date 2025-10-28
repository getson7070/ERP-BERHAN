"""Module: tenant.py — audit-added docstring. Refine with precise purpose when convenient."""
from flask import session


class TenantMixin:
    """Provide tenant-scoped query helper to mirror DB-level RLS."""

    @classmethod
    def tenant_query(cls, org_id: int | None = None):
        """Return a query filtered by the current or provided org_id."""
        if org_id is None:
            org_id = session.get("org_id")
        return cls.query.filter_by(org_id=org_id)  # type: ignore[attr-defined]



