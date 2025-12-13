"""
Role model for org-scoped RBAC.

Key principles:
- Roles are data (rows), not code.
- Roles are scoped to org_id.
- role.key is a stable machine name used by policy rules (e.g. "storekeeper", "district_manager").
- role.name is a display name (e.g. "Storekeeper", "District Manager").
"""

from __future__ import annotations

from sqlalchemy import func

from erp.extensions import db


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)

    org_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stable role identifier used by policy engine / rules
    key = db.Column(db.String(64), nullable=False, index=True)

    # Human readable role name
    name = db.Column(db.String(128), nullable=False, index=True)

    description = db.Column(db.String(255), nullable=True)

    # Whether the role is seeded/system role (prevents accidental deletion)
    is_system = db.Column(db.Boolean, nullable=False, default=False, index=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Many-to-many to permissions via role_permissions
    permissions = db.relationship(
        "Permission",
        secondary="role_permissions",
        backref=db.backref("roles", lazy="dynamic"),
        lazy="dynamic",
    )

    __table_args__ = (
        db.UniqueConstraint("org_id", "key", name="uq_roles_org_key"),
        db.Index("ix_roles_org_name", "org_id", "name"),
    )

    def __repr__(self) -> str:
        return f"<Role id={self.id} org_id={self.org_id} key={self.key!r} name={self.name!r}>"
