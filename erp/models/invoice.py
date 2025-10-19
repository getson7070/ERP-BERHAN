from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from erp.db import db

class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)

    # Link to org (tests often create org + invoices together)
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Basics
    amount   = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency = db.Column(db.String(8),    nullable=False, default="USD")
    status   = db.Column(db.String(20),   nullable=False, default="draft")  # draft|sent|paid|void

    # Dates
    issued_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date   = db.Column(db.Date,     nullable=True)
    paid_at    = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = db.relationship(
        "Organization",
        backref=db.backref("invoices", lazy=True, cascade="all, delete-orphan"),
        foreign_keys=[organization_id],
    )

    # Helpers commonly useful in tests
    @property
    def is_overdue(self) -> bool:
        return bool(self.due_date and self.status != "paid" and date.today() > self.due_date)

    def mark_paid(self) -> None:
        self.status = "paid"
        self.paid_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<Invoice {self.id} {self.status} {self.amount} {self.currency}>"
