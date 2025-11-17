"""Sales order model linking CRM opportunities with fulfilment orders."""
from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column

from erp.models import db


class SalesOrder(db.Model):
    """Represents a customer-facing sales order."""

    __tablename__ = "sales_orders"
    __table_args__ = (
        CheckConstraint("total_value >= 0", name="ck_sales_orders_total_positive"),
        Index("ix_sales_orders_org", "org_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[int | None] = mapped_column(
        db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    customer_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    posting_date: Mapped[date] = mapped_column(default=date.today, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("draft", "submitted", "delivered", "invoiced", "closed", name="sales_order_status"),
        nullable=False,
        default="draft",
    )
    total_value: Mapped[Decimal] = mapped_column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    expected_delivery: Mapped[date | None] = mapped_column(db.Date)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )


__all__ = ["SalesOrder"]
