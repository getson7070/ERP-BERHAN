"""Add commission and initiator fields to orders and gate commission eligibility."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "3f6bde5b7c29"
down_revision = "8b2f4d7c3a10"
branch_labels = None
depends_on = None


def _has_table(insp, name: str) -> bool:
    return insp.has_table(name)


def _cols(insp, table: str) -> set[str]:
    return {c["name"] for c in insp.get_columns(table)}


def _indexes(insp, table: str) -> set[str]:
    return {i["name"] for i in insp.get_indexes(table)}


def _fks(insp, table: str) -> set[str]:
    return {fk["name"] for fk in insp.get_foreign_keys(table)}


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if not _has_table(insp, "orders"):
        return

    cols = _cols(insp, "orders")
    if "payment_status" not in cols:
        op.add_column(
            "orders",
            sa.Column(
                "payment_status",
                sa.String(length=20),
                nullable=False,
                server_default="unpaid",
            ),
        )
    if "initiator_type" not in cols:
        op.add_column(
            "orders",
            sa.Column("initiator_type", sa.String(length=20), nullable=True),
        )
    if "initiator_id" not in cols:
        op.add_column("orders", sa.Column("initiator_id", sa.Integer(), nullable=True))
    if "assigned_sales_rep_id" not in cols:
        op.add_column(
            "orders",
            sa.Column("assigned_sales_rep_id", sa.Integer(), nullable=True),
        )
    if "commission_enabled" not in cols:
        op.add_column(
            "orders",
            sa.Column(
                "commission_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )
    if "commission_rate" not in cols:
        op.add_column(
            "orders",
            sa.Column(
                "commission_rate",
                sa.Numeric(5, 4),
                nullable=False,
                server_default=sa.text("0.02"),
            ),
        )
    if "commission_status" not in cols:
        op.add_column(
            "orders",
            sa.Column(
                "commission_status",
                sa.String(length=20),
                nullable=False,
                server_default="none",
            ),
        )

    idx_names = _indexes(insp, "orders")
    if "ix_orders_assigned_sales_rep_id" not in idx_names and "assigned_sales_rep_id" in _cols(insp, "orders"):
        op.create_index(
            "ix_orders_assigned_sales_rep_id",
            "orders",
            ["assigned_sales_rep_id"],
        )

    fk_names = _fks(insp, "orders")
    if (
        "fk_orders_assigned_sales_rep_id" not in fk_names
        and "assigned_sales_rep_id" in _cols(insp, "orders")
    ):
        with op.batch_alter_table("orders") as batch_op:
            batch_op.create_foreign_key(
                "fk_orders_assigned_sales_rep_id",
                "users",
                ["assigned_sales_rep_id"],
                ["id"],
                ondelete="SET NULL",
            )

    # Refresh defaults and existing rows for status/payment/commission
    if "status" in cols:
        with op.batch_alter_table("orders") as batch_op:
            batch_op.alter_column("status", server_default="submitted")
    op.execute(
        "UPDATE orders SET status = 'submitted' WHERE status IN ('draft', 'pending') OR status IS NULL"
    )
    op.execute(
        "UPDATE orders SET payment_status = 'unpaid' WHERE payment_status IS NULL"
    )
    op.execute(
        "UPDATE orders SET commission_status = CASE WHEN commission_enabled THEN 'pending' ELSE 'none' END WHERE commission_status IS NULL"
    )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if not _has_table(insp, "orders"):
        return

    if "fk_orders_assigned_sales_rep_id" in _fks(insp, "orders"):
        with op.batch_alter_table("orders") as batch_op:
            batch_op.drop_constraint("fk_orders_assigned_sales_rep_id", type_="foreignkey")

    if "ix_orders_assigned_sales_rep_id" in _indexes(insp, "orders"):
        op.drop_index("ix_orders_assigned_sales_rep_id", table_name="orders")

    cols = _cols(insp, "orders")
    for name in [
        "commission_status",
        "commission_rate",
        "commission_enabled",
        "assigned_sales_rep_id",
        "initiator_id",
        "initiator_type",
        "payment_status",
    ]:
        if name in cols:
            op.drop_column("orders", name)

    cols = _cols(insp, "orders")
    if "status" in cols:
        with op.batch_alter_table("orders") as batch_op:
            batch_op.alter_column("status", server_default=None)
