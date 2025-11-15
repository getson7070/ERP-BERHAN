"""Inventory domain model with tenant-aware helpers."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import db


class Inventory(db.Model):
    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("org_id", "sku", name="uq_inventory_org_sku"),
        Index("ix_inventory_org_id", "org_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    sku: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(default=0)
    price: Mapped[Decimal] = mapped_column(
        db.Numeric(precision=14, scale=2), default=Decimal(0)
    )

    @classmethod
    def tenant_query(cls, org_id: int):
        return cls.query.filter_by(org_id=org_id)

    def to_dict(self) -> dict[str, Decimal | int | str]:
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "sku": self.sku,
            "quantity": self.quantity,
            "price": self.price,
        }

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Inventory id={self.id} org_id={self.org_id} sku={self.sku!r}>"
