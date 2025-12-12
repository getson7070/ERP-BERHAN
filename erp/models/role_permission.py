"""Many-to-many association for roles and permissions."""

from __future__ import annotations

from erp.db import db

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), primary_key=True)

    # Backrefs handled in Role/Permission