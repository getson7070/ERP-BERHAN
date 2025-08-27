"""Database models for core ERP entities."""

from datetime import datetime
from decimal import Decimal

from . import db


class Inventory(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self) -> str:  # pragma: no cover - repr is for debugging
        return f"<Inventory {self.name}={self.quantity}>"


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    number = db.Column(db.String(64), unique=True, nullable=False)
    total = db.Column(db.Numeric(scale=2), nullable=False, default=Decimal("0.00"))
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - repr is for debugging
        return f"<Invoice {self.number} total={self.total}>"
