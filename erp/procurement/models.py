"""Procurement models covering purchase orders and order lines.

These models track the purchase order lifecycle with support for
partial receipts and returns. They intentionally avoid tight coupling
with inventory items so they can be integrated with multiple product
catalogue implementations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from erp.extensions import db


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)

    supplier_id = db.Column(db.Integer, nullable=True, index=True)
    supplier_name = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(32), nullable=False, default="draft", index=True)
    currency = db.Column(db.String(8), nullable=False, default="ETB")
    total_amount = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_by_id = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    approved_by_id = db.Column(db.Integer, nullable=True)
    cancelled_at = db.Column(db.DateTime(timezone=True), nullable=True)
    cancelled_by_id = db.Column(db.Integer, nullable=True)
    cancel_reason = db.Column(db.Text, nullable=True)

    lines = db.relationship(
        "PurchaseOrderLine",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderLine.id",
    )

    def recalc_totals(self) -> None:
        self.total_amount = sum(
            (line.ordered_quantity or Decimal("0"))
            * (line.unit_price or Decimal("0"))
            for line in self.lines
        )

    def is_modifiable(self) -> bool:
        return self.status in {"draft", "submitted"}

    def can_receive(self) -> bool:
        return self.status in {"approved", "partially_received"}

    def can_cancel(self) -> bool:
        return self.status in {"draft", "submitted", "approved"}

    def update_status_from_lines(self) -> None:
        if self.status == "cancelled":
            return

        total_ordered = sum((line.ordered_quantity or Decimal("0")) for line in self.lines)
        total_received = sum((line.received_quantity or Decimal("0")) for line in self.lines)

        if total_ordered <= 0:
            return

        if total_received == 0:
            return

        if total_received < total_ordered:
            self.status = "partially_received"
        else:
            self.status = "received"


class PurchaseOrderLine(db.Model):
    __tablename__ = "purchase_order_lines"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    purchase_order_id = db.Column(
        db.Integer,
        db.ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    item_code = db.Column(db.String(64), nullable=False)
    item_description = db.Column(db.String(255), nullable=True)

    ordered_quantity = db.Column(db.Numeric(14, 3), nullable=False)
    received_quantity = db.Column(db.Numeric(14, 3), nullable=False, default=Decimal("0"))
    returned_quantity = db.Column(db.Numeric(14, 3), nullable=False, default=Decimal("0"))

    unit_price = db.Column(db.Numeric(14, 4), nullable=False, default=Decimal("0.0000"))
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=Decimal("0.00"))

    order = db.relationship("PurchaseOrder", back_populates="lines")

    @property
    def is_fully_received(self) -> bool:
        return (self.received_quantity or Decimal("0")) >= (self.ordered_quantity or Decimal("0"))

    def receive(self, quantity: Decimal) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if (self.received_quantity or Decimal("0")) + quantity > (self.ordered_quantity or Decimal("0")):
            raise ValueError("cannot receive more than ordered")
        self.received_quantity = (self.received_quantity or Decimal("0")) + quantity

    def return_goods(self, quantity: Decimal) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if (self.returned_quantity or Decimal("0")) + quantity > (self.received_quantity or Decimal("0")):
            raise ValueError("cannot return more than received")
        self.returned_quantity = (self.returned_quantity or Decimal("0")) + quantity
