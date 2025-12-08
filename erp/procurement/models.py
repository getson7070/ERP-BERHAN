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

    pi_number = db.Column(db.String(64), nullable=True, index=True)
    awb_number = db.Column(db.String(64), nullable=True, index=True)
    hs_code = db.Column(db.String(64), nullable=True, index=True)
    bank_name = db.Column(db.String(128), nullable=True)
    customs_valuation = db.Column(db.Numeric(14, 2), nullable=True)
    efda_reference = db.Column(db.String(64), nullable=True, index=True)

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

    ticket = db.relationship(
        "ProcurementTicket",
        back_populates="purchase_order",
        uselist=False,
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


class ProcurementTicket(db.Model):
    __tablename__ = "procurement_tickets"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    purchase_order_id = db.Column(
        db.Integer,
        db.ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="submitted", index=True)
    priority = db.Column(db.String(16), nullable=False, default="normal")
    sla_due_at = db.Column(db.DateTime(timezone=True), nullable=True)
    breached_at = db.Column(db.DateTime(timezone=True), nullable=True)
    escalation_level = db.Column(db.Integer, nullable=False, default=0)

    assigned_to_id = db.Column(db.Integer, nullable=True, index=True)
    created_by_id = db.Column(db.Integer, nullable=True)
    approved_by_id = db.Column(db.Integer, nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    closed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    closed_reason = db.Column(db.Text, nullable=True)
    cancelled_at = db.Column(db.DateTime(timezone=True), nullable=True)
    cancelled_reason = db.Column(db.Text, nullable=True)

    landed_cost_total = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    landed_cost_posted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    purchase_order = db.relationship("PurchaseOrder", back_populates="ticket")
    milestones = db.relationship(
        "ProcurementMilestone",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="ProcurementMilestone.expected_at",
    )

    @property
    def sla_breached(self) -> bool:
        return self.breached_at is not None

    def evaluate_breach(self) -> None:
        if self.sla_due_at and self.status not in {"closed", "cancelled"}:
            if datetime.now(UTC) > self.sla_due_at and not self.breached_at:
                self.breached_at = datetime.now(UTC)
                self.escalation_level = max(self.escalation_level, 1)

    def mark_status(self, status: str, actor_id: int | None = None, reason: str | None = None) -> None:
        allowed = {
            "draft",
            "submitted",
            "approved",
            "in_transit",
            "customs",
            "receiving",
            "landed",
            "closed",
            "cancelled",
        }
        if status not in allowed:
            raise ValueError("invalid status")

        self.status = status

        if status == "approved":
            if not self.approved_at:
                self.approved_at = datetime.now(UTC)
            self.approved_by_id = actor_id or self.approved_by_id
        elif status == "closed":
            self.closed_at = datetime.now(UTC)
            self.closed_reason = reason or self.closed_reason
        elif status == "cancelled":
            self.cancelled_at = datetime.now(UTC)
            self.cancelled_reason = reason or self.cancelled_reason

        self.evaluate_breach()


class ProcurementMilestone(db.Model):
    __tablename__ = "procurement_milestones"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("procurement_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="pending", index=True)
    expected_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    geo_lat = db.Column(db.Float, nullable=True)
    geo_lng = db.Column(db.Float, nullable=True)
    geo_accuracy_m = db.Column(db.Float, nullable=True)
    recorded_by_id = db.Column(db.Integer, nullable=True, index=True)
    recorded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    ticket = db.relationship("ProcurementTicket", back_populates="milestones")

    def mark_completed(self) -> None:
        self.status = "completed"
        if not self.completed_at:
            self.completed_at = datetime.now(UTC)
