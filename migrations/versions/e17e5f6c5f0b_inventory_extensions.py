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


def _has_table(insp, name: str) -> bool:
    return insp.has_table(name)


def _has_col(insp, table: str, col: str) -> bool:
    return col in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # ------------------------------------------------------------------
    # 1) BOOTSTRAP CORE INVENTORY TABLES (only if missing)
    # ------------------------------------------------------------------

    if not _has_table(insp, "items"):
        op.create_table(
            "items",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("code", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=128), nullable=True),
            sa.Column("uom", sa.String(length=32), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("code", name="uq_items_code"),
        )
        op.create_index("ix_items_org", "items", ["org_id"])
        op.create_index("ix_items_name", "items", ["name"])

    if not _has_table(insp, "warehouses"):
        op.create_table(
            "warehouses",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("code", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("location", sa.String(length=255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("code", name="uq_warehouses_code"),
        )
        op.create_index("ix_warehouses_org", "warehouses", ["org_id"])

    if not _has_table(insp, "inventory_locations"):
        op.create_table(
            "inventory_locations",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "warehouse_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("warehouses.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("code", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.UniqueConstraint("warehouse_id", "code", name="uq_inventory_locations_wh_code"),
        )
        op.create_index("ix_inventory_locations_wh", "inventory_locations", ["warehouse_id"])

    if not _has_table(insp, "lots"):
        op.create_table(
            "lots",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column(
                "item_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("items.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("number", sa.String(length=64), nullable=True),
            sa.Column("expiry_date", sa.Date(), nullable=True),
            sa.Column("manufacture_date", sa.Date(), nullable=True),
            sa.Column("received_date", sa.Date(), nullable=True),
            sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_lots_item", "lots", ["item_id"])
        op.create_index("ix_lots_org", "lots", ["org_id"])

    if not _has_table(insp, "inventory_serials"):
        op.create_table(
            "inventory_serials",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column(
                "item_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("items.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("serial_number", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("item_id", "serial_number", name="uq_inventory_serial_item_serial"),
        )
        op.create_index("ix_inventory_serial_item", "inventory_serials", ["item_id"])

    if not _has_table(insp, "stock_balances"):
        op.create_table(
            "stock_balances",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column(
                "item_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("items.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "warehouse_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("warehouses.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "location_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("inventory_locations.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "lot_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("lots.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("qty_on_hand", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
            sa.Column("reserved_qty", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint(
                "item_id",
                "warehouse_id",
                "location_id",
                "lot_id",
                name="uq_stock_balances_key",
            ),
        )
        op.create_index("ix_stock_bal_item_wh", "stock_balances", ["item_id", "warehouse_id"])

    if not _has_table(insp, "stock_ledger_entries"):
        op.create_table(
            "stock_ledger_entries",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column(
                "item_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("items.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "warehouse_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "location_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("inventory_locations.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "lot_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("lots.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("transaction_type", sa.String(length=32), nullable=False),
            sa.Column("qty", sa.Numeric(14, 2), nullable=False),
            sa.Column("balance_after", sa.Numeric(14, 2), nullable=True),
            sa.Column("reference", sa.String(length=128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_sle_item_wh", "stock_ledger_entries", ["item_id", "warehouse_id"])

    if not _has_table(insp, "cycle_counts"):
        op.create_table(
            "cycle_counts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column(
                "warehouse_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
            sa.Column("count_date", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_cycle_counts_wh", "cycle_counts", ["warehouse_id"])

    if not _has_table(insp, "cycle_count_lines"):
        op.create_table(
            "cycle_count_lines",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "cycle_count_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("cycle_counts.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "item_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("items.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("expected_qty", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
            sa.Column("counted_qty", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
            sa.Column("variance_qty", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
        )
        op.create_index("ix_cycle_count_lines_cc", "cycle_count_lines", ["cycle_count_id"])

    if not _has_table(insp, "reorders"):
        op.create_table(
            "reorders",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column(
                "item_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("items.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "warehouse_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("warehouses.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("min_qty", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
            sa.Column("reorder_qty", sa.Numeric(14, 2), nullable=False, server_default=sa.text("0")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("item_id", "warehouse_id", name="uq_reorders_item_wh"),
        )
        op.create_index("ix_reorders_item_wh", "reorders", ["item_id", "warehouse_id"])

    if not _has_table(insp, "stock_transfers"):
        op.create_table(
            "stock_transfers",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column(
                "from_warehouse_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "to_warehouse_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
            sa.Column("reference", sa.String(length=128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_stock_transfers_org", "stock_transfers", ["org_id"])

    # ------------------------------------------------------------------
    # 2) APPLY EXTENSIONS SAFELY (guards for old DBs)
    # ------------------------------------------------------------------

    # warehouses: ensure org_id column exists
    if _has_table(insp, "warehouses") and not _has_col(insp, "warehouses", "org_id"):
        op.add_column("warehouses", sa.Column("org_id", sa.Integer(), nullable=True))
        op.create_index("ix_warehouses_org", "warehouses", ["org_id"])

    # stock_ledger_entries: optional linkage columns
    if _has_table(insp, "stock_ledger_entries") and not _has_col(insp, "stock_ledger_entries", "location_id"):
        op.add_column(
            "stock_ledger_entries",
            sa.Column(
                "location_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("inventory_locations.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    if _has_table(insp, "stock_ledger_entries") and not _has_col(insp, "stock_ledger_entries", "lot_id"):
        op.add_column(
            "stock_ledger_entries",
            sa.Column(
                "lot_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("lots.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    # cycle_counts: ensure status column exists
    if _has_table(insp, "cycle_counts") and not _has_col(insp, "cycle_counts", "status"):
        op.add_column(
            "cycle_counts",
            sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        )

    # reorders: ensure is_active exists
    if _has_table(insp, "reorders") and not _has_col(insp, "reorders", "is_active"):
        op.add_column(
            "reorders",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # reverse-safe drops (only if table exists)
    for table in [
        "stock_transfers",
        "reorders",
        "cycle_count_lines",
        "cycle_counts",
        "stock_ledger_entries",
        "stock_balances",
        "inventory_serials",
        "lots",
        "inventory_locations",
        "warehouses",
        "items",
    ]:
        if _has_table(insp, table):
            op.drop_table(table)
