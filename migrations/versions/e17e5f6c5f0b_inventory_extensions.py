"""Inventory extensions for warehouses, ledger, cycle counts, and reorders."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect  # For idempotency

revision = "e17e5f6c5f0b"
down_revision = "d0b1b1c4f7a0"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # Create warehouses if missing
    if "warehouses" not in tables:
        op.create_table(
            "warehouses",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("code", sa.String(length=32), nullable=True, unique=True),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_warehouses_org", "warehouses", ["org_id"])

    # Safe add org_id to warehouses
    existing_cols = {col["name"] for col in inspector.get_columns("warehouses")}
    if "org_id" not in existing_cols:
        op.add_column("warehouses", sa.Column("org_id", sa.Integer(), nullable=False))
        op.execute("UPDATE warehouses SET org_id = 1 WHERE org_id IS NULL")

    # Create inventory_ledger if missing
    if "inventory_ledger" not in tables:
        op.create_table(
            "inventory_ledger",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("item_id", sa.Integer(), nullable=False, index=True),
            sa.Column("warehouse_id", sa.Integer(), nullable=False, index=True),
            sa.Column("transaction_type", sa.String(length=32), nullable=False),
            sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
            sa.Column("unit_cost", sa.Numeric(12, 4), nullable=True),
            sa.Column("total_cost", sa.Numeric(14, 2), nullable=True),
            sa.Column("reference_id", sa.String(length=128), nullable=True),
            sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_inventory_ledger_org", "inventory_ledger", ["org_id"])
        op.create_index("ix_inventory_ledger_item", "inventory_ledger", ["item_id"])
        op.create_index("ix_inventory_ledger_warehouse", "inventory_ledger", ["warehouse_id"])

    # Safe FKs for inventory_ledger
    fk_names = {fk["name"] for fk in inspector.get_foreign_keys("inventory_ledger")}
    if "fk_inventory_ledger_item" not in fk_names:
        with op.batch_alter_table("inventory_ledger", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_inventory_ledger_item",
                "inventory_items",
                ["item_id"],
                ["id"],
                ondelete="CASCADE",
            )
    if "fk_inventory_ledger_warehouse" not in fk_names:
        with op.batch_alter_table("inventory_ledger", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_inventory_ledger_warehouse",
                "warehouses",
                ["warehouse_id"],
                ["id"],
                ondelete="CASCADE",
            )

    # Create cycle_counts if missing
    if "cycle_counts" not in tables:
        op.create_table(
            "cycle_counts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("warehouse_id", sa.Integer(), nullable=False, index=True),
            sa.Column("item_id", sa.Integer(), nullable=False, index=True),
            sa.Column("count_date", sa.Date(), nullable=False),
            sa.Column("expected_qty", sa.Numeric(12, 3), nullable=False),
            sa.Column("counted_qty", sa.Numeric(12, 3), nullable=False),
            sa.Column("variance", sa.Numeric(12, 3), nullable=False),
            sa.Column("adjustment_reason", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("approved_by_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_cycle_counts_org", "cycle_counts", ["org_id"])
        op.create_index("ix_cycle_counts_warehouse", "cycle_counts", ["warehouse_id"])
        op.create_index("ix_cycle_counts_item", "cycle_counts", ["item_id"])

    # Safe FKs for cycle_counts
    fk_names = {fk["name"] for fk in inspector.get_foreign_keys("cycle_counts")}
    if "fk_cycle_counts_warehouse" not in fk_names:
        with op.batch_alter_table("cycle_counts", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_cycle_counts_warehouse",
                "warehouses",
                ["warehouse_id"],
                ["id"],
                ondelete="CASCADE",
            )
    if "fk_cycle_counts_item" not in fk_names:
        with op.batch_alter_table("cycle_counts", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_cycle_counts_item",
                "inventory_items",
                ["item_id"],
                ["id"],
                ondelete="CASCADE",
            )

    # Create reorder_policies if missing
    if "reorder_policies" not in tables:
        op.create_table(
            "reorder_policies",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("item_id", sa.Integer(), nullable=False, index=True),
            sa.Column("warehouse_id", sa.Integer(), nullable=False, index=True),
            sa.Column("reorder_point", sa.Numeric(12, 3), nullable=False),
            sa.Column("reorder_qty", sa.Numeric(12, 3), nullable=False),
            sa.Column("lead_time_days", sa.Integer(), nullable=False),
            sa.Column("safety_stock", sa.Numeric(12, 3), nullable=False),
            sa.Column("supplier_id", sa.Integer(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_reorder_policies_org", "reorder_policies", ["org_id"])
        op.create_index("ix_reorder_policies_item", "reorder_policies", ["item_id"])
        op.create_index("ix_reorder_policies_warehouse", "reorder_policies", ["warehouse_id"])

    # Safe FKs for reorder_policies
    fk_names = {fk["name"] for fk in inspector.get_foreign_keys("reorder_policies")}
    if "fk_reorder_policies_item" not in fk_names:
        with op.batch_alter_table("reorder_policies", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_reorder_policies_item",
                "inventory_items",
                ["item_id"],
                ["id"],
                ondelete="CASCADE",
            )
    if "fk_reorder_policies_warehouse" not in fk_names:
        with op.batch_alter_table("reorder_policies", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_reorder_policies_warehouse",
                "warehouses",
                ["warehouse_id"],
                ["id"],
                ondelete="CASCADE",
            )


def downgrade():
    # Drop in reverse (FKs first)
    with op.batch_alter_table("reorder_policies", schema=None) as batch_op:
        batch_op.drop_constraint("fk_reorder_policies_warehouse", type_="foreignkey")
        batch_op.drop_constraint("fk_reorder_policies_item", type_="foreignkey")

    op.drop_index("ix_reorder_policies_warehouse", table_name="reorder_policies")
    op.drop_index("ix_reorder_policies_item", table_name="reorder_policies")
    op.drop_index("ix_reorder_policies_org", table_name="reorder_policies")
    op.drop_table("reorder_policies")

    with op.batch_alter_table("cycle_counts", schema=None) as batch_op:
        batch_op.drop_constraint("fk_cycle_counts_item", type_="foreignkey")
        batch_op.drop_constraint("fk_cycle_counts_warehouse", type_="foreignkey")

    op.drop_index("ix_cycle_counts_item", table_name="cycle_counts")
    op.drop_index("ix_cycle_counts_warehouse", table_name="cycle_counts")
    op.drop_index("ix_cycle_counts_org", table_name="cycle_counts")
    op.drop_table("cycle_counts")

    with op.batch_alter_table("inventory_ledger", schema=None) as batch_op:
        batch_op.drop_constraint("fk_inventory_ledger_warehouse", type_="foreignkey")
        batch_op.drop_constraint("fk_inventory_ledger_item", type_="foreignkey")

    op.drop_index("ix_inventory_ledger_warehouse", table_name="inventory_ledger")
    op.drop_index("ix_inventory_ledger_item", table_name="inventory_ledger")
    op.drop_index("ix_inventory_ledger_org", table_name="inventory_ledger")
    op.drop_table("inventory_ledger")

    op.drop_index("ix_warehouses_org", table_name="warehouses")
    op.drop_column("warehouses", "org_id")
    op.drop_table("warehouses")