"""Employee directory model scoped to an organisation.

This model remains deliberately simple and backwards-compatible:

- Keeps INTEGER primary key `id` and existing columns unchanged.
- Adds a *secondary* UUID column `uuid` as a stable public identifier.
- Adds helper properties:
    - full_name
    - is_management
    - is_supervisor

Management vs Supervisor classification here is based on the free-text
`role` field (e.g. "Technical Manager", "Senior Accountant",
"Sales Supervisor"). This complements the RBAC role model on `User`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from erp.models import db  # re-exported from erp.models.__init__

try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
except Exception:  # pragma: no cover
    PG_UUID = db.String  # type: ignore[assignment]


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)

    # New: UUID as secondary identifier (for APIs, URLs, etc.)
    uuid = db.Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        unique=True,
        default=uuid4,
        index=True,
    )

    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)

    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    phone = db.Column(db.String(50))

    # Free-text “business role title” – e.g. "Technical Manager",
    # "Sales Supervisor", "Senior Accountant", etc.
    role = db.Column(db.String(120), default="staff")

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Tenant / organisation scoping
    # ------------------------------------------------------------------
    @classmethod
    def tenant_query(cls, org_id: int | None = None):
        """Convenience helper to scope queries by organisation."""
        query = cls.query
        if org_id is not None:
            query = query.filter_by(organization_id=org_id)
        return query

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def public_id(self) -> str:
        """Stable, non-guessable identifier for external exposure."""
        return str(self.uuid)

    # ------------------------------------------------------------------
    # Management / Supervisor classification based on the `role` text
    # ------------------------------------------------------------------
    @property
    def role_normalized(self) -> str:
        """Lowercased, trimmed version of role for classification."""
        return (self.role or "").strip().lower()

    @property
    def is_management(self) -> bool:
        """
        Treat this employee as Management.

        Examples:
          - "technical manager"
          - "finance manager"
          - "warehouse manager"
          - "hr manager"
          - "marketing manager"
          - "general manager"
          - "operations manager"
          - "managing director"
        """
        r = self.role_normalized
        if not r:
            return False

        # Direct keywords
        management_keywords = [
            "technical manager",
            "finance manager",
            "warehouse manager",
            "hr manager",
            "human resource manager",
            "marketing manager",
            "general manager",
            "operations manager",
            "managing director",
            "director",
        ]

        for kw in management_keywords:
            if kw in r:
                return True

        # Fallback: any role containing "manager" but not obviously an assistant
        if "manager" in r and "assistant" not in r:
            return True

        return False

    @property
    def is_supervisor(self) -> bool:
        """
        Treat this employee as Supervisor-level but not full Management.

        Examples:
          - "sales supervisor"
          - "senior accountant"
          - "senior purchaser"
          - "service supervisor"
          - "team leader"
        """
        # If already classified as management, we don’t downgrade.
        if self.is_management:
            return False

        r = self.role_normalized
        if not r:
            return False

        supervisor_keywords = [
            "sales supervisor",
            "service supervisor",
            "supervisor",
            "team leader",
            "team lead",
            "senior accountant",
            "senior purchaser",
            "senior buyer",
        ]

        for kw in supervisor_keywords:
            if kw in r:
                return True

        # Generic heuristic: "senior" but not manager/director
        if "senior" in r and "manager" not in r and "director" not in r:
            return True

        return False

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"<Employee id={self.id!r} uuid={self.uuid!s} "
            f"org_id={self.organization_id!r} "
            f"email={self.email!r} role={self.role!r}>"
        )
