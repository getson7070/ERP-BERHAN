"""Create procurement purchase order tables."""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6b4de6d7a0a1"
down_revision: Union[str, None] = "ce91d3657d20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "purchase_orders" not in inspector.get_table_names():
        op.create_table(
            "purchase_orders",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), nullable=False),
            sa.Column("supplier_id", sa.Integer(), nullable=True),
            sa.Column("supplier_name", sa.String(length=255), nullable=True),
            sa.Column(
                "status",
                sa.String(length=32),
                nullable=False,
                server_default="draft",
            ),
            sa.Column("currency", sa.String(length=8), nullable=False, server_default="ETB"),
            sa.Column(
                "total_amount",
                sa.Numeric(precision=14, scale=2),
                nullable=False,
                server_default="0",
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_by_id", sa.Integer(), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_by_id", sa.Integer(), nullable=True),
            sa.Column("cancel_reason", sa.Text(), nullable=True),
        )
        op.create_index(
            "ix_purchase_orders_org_id", "purchase_orders", ["organization_id"], unique=False
        )
        op.create_index(
            "ix_purchase_orders_supplier_id", "purchase_orders", ["supplier_id"], unique=False
        )
        op.create_index(
            "ix_purchase_orders_status", "purchase_orders", ["status"], unique=False
        )

    if "purchase_order_lines" not in inspector.get_table_names():
        op.create_table(
            "purchase_order_lines",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), nullable=False),
            sa.Column("purchase_order_id", sa.Integer(), nullable=False),
            sa.Column("item_code", sa.String(length=64), nullable=False),
            sa.Column("item_description", sa.String(length=255), nullable=True),
            sa.Column("ordered_quantity", sa.Numeric(precision=14, scale=3), nullable=False),
            sa.Column(
                "received_quantity",
                sa.Numeric(precision=14, scale=3),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "returned_quantity",
                sa.Numeric(precision=14, scale=3),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "unit_price",
                sa.Numeric(precision=14, scale=4),
                nullable=False,
                server_default="0",
            ),
            sa.Column("tax_rate", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint([
                "purchase_order_id",
            ], ["purchase_orders.id"], ondelete="CASCADE"),
        )
        op.create_index(
            "ix_purchase_order_lines_org_id", "purchase_order_lines", ["organization_id"], unique=False
        )
        op.create_index(
            "ix_purchase_order_lines_po_id", "purchase_order_lines", ["purchase_order_id"], unique=False
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "purchase_order_lines" in inspector.get_table_names():
        op.drop_index("ix_purchase_order_lines_po_id", table_name="purchase_order_lines")
        op.drop_index("ix_purchase_order_lines_org_id", table_name="purchase_order_lines")
        op.drop_table("purchase_order_lines")

    if "purchase_orders" in inspector.get_table_names():
        op.drop_index("ix_purchase_orders_status", table_name="purchase_orders")
        op.drop_index("ix_purchase_orders_supplier_id", table_name="purchase_orders")
        op.drop_index("ix_purchase_orders_org_id", table_name="purchase_orders")
        op.drop_table("purchase_orders")
