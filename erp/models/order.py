from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from erp.db import db

class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    # Likely relations used in tests
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status = db.Column(db.String(20), nullable=False, default="pending")  # pending|paid|shipped|canceled
    currency = db.Column(db.String(8), nullable=False, default="USD")
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    placed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    shipped_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship(
        "Organization",
        backref=db.backref("orders", lazy=True, cascade="all, delete-orphan"),
        foreign_keys=[organization_id],
    )
    user = db.relationship(
        "User",
        backref=db.backref("orders", lazy=True),
        foreign_keys=[user_id],
    )

    # handy helpers
    def mark_paid(self):
        self.status = "paid"
        self.paid_at = datetime.utcnow()

    def mark_shipped(self):
        self.status = "shipped"
        self.shipped_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<Order {self.id} {self.status} {self.total_amount} {self.currency}>"
