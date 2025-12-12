"""Permission model for granular access control."""

from __future__ import annotations

from erp.db import db

class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)  # e.g., 'view_orders'
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Permission id={self.id} name={self.name}>"