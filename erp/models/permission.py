"""Permission model for granular access control."""

from __future__ import annotations

from erp.db import db


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)

    # Keep as the canonical permission key (your existing code expects this).
    # Examples: "view_orders", "tenders.manage", "discounts.approve"
    name = db.Column(db.String(128), unique=True, nullable=False, index=True)

    # Optional grouping; safe to keep nullable
    module = db.Column(db.String(64), nullable=True, index=True)

    description = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Permission id={self.id} name={self.name}>"
