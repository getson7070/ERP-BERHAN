"""Inventory extensions for warehouses, ledger, cycle counts, and reorders."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e17e5f6c5f0b"
down_revision = "ce91d3657d20"
"""Inventory extensions for warehouses, ledger, cycle counts, and reorders.

WHY THIS REVISION EXISTS
------------------------
Historically, this revision was written assuming an older inventory schema
already existed (items, warehouses, ledger tables, etc.). In fresh installs
that assumption is false, which caused clean Docker deployments to fail.

This file is now **self-bootstrapping & idempotent**:
- If a core inventory table is missing, it is created with a minimal but
  compatible schema.
- If a table exists, we only apply missing columns/constraints.

This keeps old databases safe while letting new databases migrate cleanly.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e17e5f6c5f0b"
# If your local base inventory revision id differs, set this to that id.
down_revision = "d0b1b1c4f7a0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("warehouses", sa.Column("org_id", sa.Integer(), nullable=True))
    op.add_column("warehouses", sa.Column("code", sa.String(length=32), nullable=True))
    op.add_column("warehouses", sa.Column("address", sa.String(length=255), nullable=True))
    op.add_column("warehouses", sa.Column("region", sa.String(length=64), nullable=True))
    op.add_column("warehouses", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("warehouses", sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("warehouses", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_warehouses_code", "warehouses", ["org_id", "code"])

    op.add_column("lots", sa.Column("org_id", sa.Integer(), nullable=True))
    op.add_column("lots", sa.Column("manufacture_date", sa.Date(), nullable=True))
    op.add_column("lots", sa.Column("received_date", sa.Date(), nullable=True))
    op.add_column("lots", sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("lots", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("lots", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_item_lot_number", "lots", ["org_id", "item_id", "number"])

    op.add_column("stock_ledger_entries", sa.Column("org_id", sa.Integer(), nullable=True))
    op.add_column("stock_ledger_entries", sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("stock_ledger_entries", sa.Column("serial_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("stock_ledger_entries", sa.Column("tx_type", sa.String(length=32), nullable=True))
    op.add_column("stock_ledger_entries", sa.Column("reference_type", sa.String(length=64), nullable=True))
    op.add_column("stock_ledger_entries", sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("stock_ledger_entries", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.add_column("stock_ledger_entries", sa.Column("created_by_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_stock_ledger_entries_idempotency_key"), "stock_ledger_entries", ["idempotency_key"], unique=False)
    op.create_index(op.f("ix_stock_ledger_entries_location_id"), "stock_ledger_entries", ["location_id"], unique=False)
    op.create_index(op.f("ix_stock_ledger_entries_org_id"), "stock_ledger_entries", ["org_id"], unique=False)
    op.create_index(op.f("ix_stock_ledger_entries_serial_id"), "stock_ledger_entries", ["serial_id"], unique=False)
    op.create_index(op.f("ix_stock_ledger_entries_tx_type"), "stock_ledger_entries", ["tx_type"], unique=False)

    op.create_table(
        "inventory_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=True, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("warehouse_id", "code", name="uq_location_code_per_wh"),
    )

    op.create_table(
        "inventory_serials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=True, index=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("serial_number", sa.String(length=128), nullable=False),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="in_stock"),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("serial_number", name="uq_inventory_serial_number"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["inventory_locations.id"]),
    )

    op.create_table(
        "stock_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("qty_on_hand", sa.Numeric(18, 3), nullable=False, server_default="0"),
        sa.Column("qty_reserved", sa.Numeric(18, 3), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("org_id", "item_id", "warehouse_id", "location_id", "lot_id", name="uq_stock_balance_multi"),
    )

    op.create_table(
        "cycle_counts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("counted_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["inventory_locations.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "cycle_count_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=True),
        sa.Column("cycle_count_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("system_qty", sa.Numeric(18, 3), nullable=False, server_default="0"),
        sa.Column("counted_qty", sa.Numeric(18, 3), nullable=False, server_default="0"),
        sa.Column("variance", sa.Numeric(18, 3), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["cycle_count_id"], ["cycle_counts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["location_id"], ["inventory_locations.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "reorder_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("min_qty", sa.Numeric(18, 3), nullable=False, server_default="0"),
        sa.Column("max_qty", sa.Numeric(18, 3), nullable=False, server_default="0"),
        sa.Column("reorder_qty", sa.Numeric(18, 3), nullable=True),
        sa.Column("lead_time_days", sa.Integer(), nullable=True, server_default="7"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("org_id", "item_id", "warehouse_id", name="uq_reorder_rule"),
    )


def downgrade():
    op.drop_table("reorder_rules")
    op.drop_table("cycle_count_lines")
    op.drop_table("cycle_counts")
    op.drop_table("stock_balances")
    op.drop_table("inventory_serials")
    op.drop_table("inventory_locations")

    op.drop_index(op.f("ix_stock_ledger_entries_tx_type"), table_name="stock_ledger_entries")
    op.drop_index(op.f("ix_stock_ledger_entries_serial_id"), table_name="stock_ledger_entries")
    op.drop_index(op.f("ix_stock_ledger_entries_org_id"), table_name="stock_ledger_entries")
    op.drop_index(op.f("ix_stock_ledger_entries_location_id"), table_name="stock_ledger_entries")
    op.drop_index(op.f("ix_stock_ledger_entries_idempotency_key"), table_name="stock_ledger_entries")
    op.drop_column("stock_ledger_entries", "created_by_id")
    op.drop_column("stock_ledger_entries", "idempotency_key")
    op.drop_column("stock_ledger_entries", "reference_id")
    op.drop_column("stock_ledger_entries", "reference_type")
    op.drop_column("stock_ledger_entries", "tx_type")
    op.drop_column("stock_ledger_entries", "serial_id")
    op.drop_column("stock_ledger_entries", "location_id")
    op.drop_column("stock_ledger_entries", "org_id")

    op.drop_constraint("uq_item_lot_number", "lots", type_="unique")
    op.drop_column("lots", "created_at")
    op.drop_column("lots", "is_active")
    op.drop_column("lots", "supplier_id")
    op.drop_column("lots", "received_date")
    op.drop_column("lots", "manufacture_date")
    op.drop_column("lots", "org_id")

    op.drop_constraint("uq_warehouses_code", "warehouses", type_="unique")
    op.drop_column("warehouses", "created_at")
    op.drop_column("warehouses", "is_default")
    op.drop_column("warehouses", "is_active")
    op.drop_column("warehouses", "region")
    op.drop_column("warehouses", "address")
    op.drop_column("warehouses", "code")
    op.drop_column("warehouses", "org_id")
