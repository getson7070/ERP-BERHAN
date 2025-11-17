"""Module: supplychain/models.py — audit-added docstring. Refine with precise purpose when convenient."""

import uuid

from erp.extensions import db
from sqlalchemy import Index

class ReorderPolicy(db.Model):
    __tablename__ = "reorder_policies"
    __table_args__ = (
        Index("ix_reorder_policies_org", "org_id"),
        Index("ix_reorder_policies_item", "item_id"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    item_id = db.Column(db.String(36), nullable=False)
    warehouse_id = db.Column(db.String(36), nullable=False)
    service_level = db.Column(db.Numeric(4, 2), default=0.95)
    safety_stock = db.Column(db.Numeric(18, 3), default=0)
    reorder_point = db.Column(db.Numeric(18, 3), default=0)



