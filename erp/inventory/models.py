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
    # Legacy deployments stored only a name; code/address add compatibility for Task 8 flows
    code = db.Column(db.String(32), nullable=True, index=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    region = db.Column(db.String(64), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("org_id", "code", name="uq_warehouses_code"),)


class InventoryLocation(db.Model):
    """Bin / shelf inside a warehouse."""

    __tablename__ = "inventory_locations"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    warehouse_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code = db.Column(db.String(64), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    warehouse = db.relationship("Warehouse", backref="locations")

    __table_args__ = (UniqueConstraint("warehouse_id", "code", name="uq_location_code_per_wh"),)


class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    def expiry_date(self) -> date | None:  # compatibility alias
        return self.expiry


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
    location_id = db.Column(UUID(as_uuid=True), db.ForeignKey("inventory_locations.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("serial_number", name="uq_inventory_serial_number"),)


class StockBalance(db.Model):
    """Current on-hand quantity per item/location/lot with row locking support."""

    __tablename__ = "stock_balances"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    location_id = db.Column(UUID(as_uuid=True), db.ForeignKey("inventory_locations.id"), nullable=True, index=True)
    lot_id = db.Column(UUID(as_uuid=True), db.ForeignKey("lots.id"), nullable=True, index=True)
    qty_on_hand = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    qty_reserved = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("org_id", "item_id", "warehouse_id", "location_id", "lot_id", name="uq_stock_balance_multi"),
    )


class StockLedgerEntry(db.Model):
    """Immutable stock movement ledger with idempotency keys for replay safety."""

    __tablename__ = "stock_ledger_entries"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    posting_time = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    location_id = db.Column(UUID(as_uuid=True), db.ForeignKey("inventory_locations.id"), nullable=True, index=True)
    lot_id = db.Column(UUID(as_uuid=True), db.ForeignKey("lots.id"), nullable=True, index=True)
    serial_id = db.Column(UUID(as_uuid=True), db.ForeignKey("inventory_serials.id"), nullable=True, index=True)
    qty = db.Column(db.Numeric(18, 3), nullable=False)  # +in / -out
    rate = db.Column(db.Numeric(18, 4), nullable=False, default=Decimal("0"))
    value = db.Column(db.Numeric(18, 2), nullable=False, default=Decimal("0"))
    tx_type = db.Column(db.String(32), nullable=True, index=True)
    voucher_type = db.Column(db.String(32))
    voucher_id = db.Column(UUID(as_uuid=True))
    reference_type = db.Column(db.String(64), nullable=True)
    reference_id = db.Column(UUID(as_uuid=True), nullable=True)
    idempotency_key = db.Column(db.String(128), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, nullable=True)


class CycleCount(db.Model):
    """Cycle count header for variance approvals."""

    __tablename__ = "cycle_counts"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id"), nullable=False, index=True)
    location_id = db.Column(UUID(as_uuid=True), db.ForeignKey("inventory_locations.id"), nullable=True, index=True)
    status = db.Column(db.String(32), nullable=False, default="open", index=True)
    counted_by_id = db.Column(db.Integer, nullable=True)
    approved_by_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    lines = db.relationship("CycleCountLine", back_populates="cycle_count", cascade="all, delete-orphan")


class CycleCountLine(db.Model):
    __tablename__ = "cycle_count_lines"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    cycle_count_id = db.Column(UUID(as_uuid=True), db.ForeignKey("cycle_counts.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    lot_id = db.Column(UUID(as_uuid=True), db.ForeignKey("lots.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = db.Column(UUID(as_uuid=True), db.ForeignKey("inventory_locations.id", ondelete="SET NULL"), nullable=True, index=True)
    system_qty = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    counted_qty = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    variance = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))

    cycle_count = db.relationship("CycleCount", back_populates="lines")


class ReorderRule(db.Model):
    """Auto-reorder thresholds per item/warehouse."""

    __tablename__ = "reorder_rules"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(db.Integer, nullable=True, index=True)
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = db.Column(UUID(as_uuid=True), db.ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    min_qty = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    max_qty = db.Column(db.Numeric(18, 3), nullable=False, default=Decimal("0"))
    reorder_qty = db.Column(db.Numeric(18, 3), nullable=True)
    lead_time_days = db.Column(db.Integer, nullable=True, default=7)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("org_id", "item_id", "warehouse_id", name="uq_reorder_rule"),)
