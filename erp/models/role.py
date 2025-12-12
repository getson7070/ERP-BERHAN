"""Role model for dynamic RBAC."""

from __future__ import annotations

from datetime import UTC, datetime
from erp.db import db
from erp.models.permission import Permission  # UPGRADE: Import for relationship
from erp.models.role_permission import RolePermission

class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # UPGRADE: Add relationships for dynamic RBAC (preserves original schema)
    permissions = db.relationship('Permission', secondary='role_permissions', backref='roles')

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name}>"