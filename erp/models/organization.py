"""
Organization (Tenant) model.

An Organization represents a legal entity / institution:
- Clients: institutions identified by a 10-digit TIN
- Internal: Berhan Pharma / related entities (also can have a TIN)

Users belong to an organization via users.org_id.
All RBAC, departments, teams, and policies are scoped by org_id.
"""

from __future__ import annotations

from sqlalchemy import func

from erp.extensions import db


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)

    # Public identifier (safe to expose in URLs/APIs)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)

    # Ethiopian TIN: 10 digits, may start with 0. Stored as string to preserve leading zeros.
    tin = db.Column(db.String(10), unique=True, nullable=False, index=True)

    name = db.Column(db.String(255), nullable=False, index=True)

    # Optional classification; keep flexible for later
    org_type = db.Column(db.String(32), nullable=True, index=True)  # e.g. "client", "internal"

    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        db.UniqueConstraint("tin", name="uq_org_tin"),
        db.UniqueConstraint("uuid", name="uq_org_uuid"),
    )

    def __repr__(self) -> str:
        return f"<Organization id={self.id} tin={self.tin!r} name={self.name!r}>"
