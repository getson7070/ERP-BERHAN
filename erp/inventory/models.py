"""Inventory domain models with multi-warehouse, lots, serials, and ledger support."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, date
from decimal import Decimal

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from ..extensions import db


class Warehouse(db.Model):
    """Physical warehouse record (legacy-friendly with added metadata)."""

    __tablename__ = "warehouses"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(64), nullable=True, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Item(db.Model):
    """Catalog item with org scoping and minimal fields kept for back-compat."""

    __tablename__ = "items"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    sku = db.Column(db.String(64), unique=True, nullable=False)   # keep template compatibility
    name = db.Column(db.String(255), nullable=False)
    uom = db.Column(db.String(32), default="Unit")


class Lot(db.Model):
    """Lot/batch with optional expiry tracking."""

    __tablename__ = "lots"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id"), nullable=False, index=True)
    number = db.Column(db.String(64), index=True)
    expiry = db.Column("expiry", db.Date)
    manufacture_date = db.Column(db.Date, nullable=True)
    received_date = db.Column(db.Date, nullable=True)
    supplier_id = db.Column(UUID(as_uuid=True), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("org_id", "item_id", "number", name="uq_item_lot_number"),)

    @property
    def lot_number(self) -> str | None:
        """Back-compat name used in tests."""
        return self.number

    @lot_number.setter
    def lot_number(self, value: str | None) -> None:
        self.number = value

    @property
    def expiry_date(self) -> date | None:
        return self.expiry

    @expiry_date.setter
    def expiry_date(self, value: date | None) -> None:
        self.expiry = value


class InventorySerial(db.Model):
    """Per-unit serial tracking with optional lot linkage."""

    __tablename__ = "inventory_serials"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    serial_number = db.Column(db.String(128), nullable=False, index=True)
    lot_id = db.Column(UUID(as_uuid=True), db.ForeignKey("lots.id", ondelete="SET NULL"), nullable=True, index=True)
    status = db.Column(db.String(32), nullable=False, default="in_stock")
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("org_id", "item_id", "serial_number", name="uq_item_serial_number"),)


class StockBalance(db.Model):
    """Aggregated quantity per item/warehouse."""

    __tablename__ = "stock_balances"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    qty_on_hand = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("org_id", "item_id", "warehouse_id", name="uq_org_item_warehouse"),)


class StockLedgerEntry(db.Model):
    """Immutable stock movement log."""

    __tablename__ = "stock_ledger_entries"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    lot_id = db.Column(UUID(as_uuid=True), db.ForeignKey("lots.id"), nullable=True, index=True)
    serial_id = db.Column(UUID(as_uuid=True), db.ForeignKey("inventory_serials.id"), nullable=True, index=True)
    quantity_delta = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    reason = db.Column(db.String(255), nullable=True)
    reference_type = db.Column(db.String(64), nullable=True)
    reference_id = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CycleCount(db.Model):
    """Cycle-count document (header)."""

    __tablename__ = "cycle_counts"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    scheduled_for = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="scheduled")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    lines = db.relationship("CycleCountLine", back_populates="cycle_count", cascade="all, delete-orphan")


class InventoryLocation(db.Model):
    """Specific physical/bin location inside a warehouse."""

    __tablename__ = "inventory_locations"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    code = db.Column(db.String(64), nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CycleCountLine(db.Model):
    """Line item for a cycle count."""

    __tablename__ = "cycle_count_lines"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    cycle_count_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("cycle_counts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    lot_id = db.Column(UUID(as_uuid=True), db.ForeignKey("lots.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("inventory_locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    system_qty = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    counted_qty = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    variance = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))

    cycle_count = db.relationship("CycleCount", back_populates="lines")


class ReorderRule(db.Model):
    """Auto-reorder thresholds per item/warehouse."""

    __tablename__ = "reorder_rules"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    item_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    warehouse_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("warehouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    min_qty = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    max_qty = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    reorder_qty = db.Column(db.Numeric(18, 3), nullable=True)
    lead_time_days = db.Column(db.Integer, nullable=True, default=7)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("org_id", "item_id", "warehouse_id", name="uq_reorder_rule"),)


# Backwards-compatible alias for tests and services
SerialNumber = InventorySerial

__all__ = [
    "Warehouse",
    "Item",
    "Lot",
    "InventorySerial",
    "SerialNumber",
    "StockBalance",
    "StockLedgerEntry",
    "CycleCount",
    "CycleCountLine",
    "InventoryLocation",
    "ReorderRule",
]