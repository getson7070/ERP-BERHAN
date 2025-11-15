"""create inventory items table

Revision ID: d0b1b1c4f7a0
Revises: 1f2e3d4c5b6a
Create Date: 2025-11-15 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d0b1b1c4f7a0"
down_revision: Union[str, None] = "1f2e3d4c5b6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the inventory_items table with tenant safeguards."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "inventory_items" in inspector.get_table_names():
        return

    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "price",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_index("ix_inventory_org_id", "inventory_items", ["org_id"], unique=False)
    op.create_unique_constraint(
        "uq_inventory_org_sku",
        "inventory_items",
        ["org_id", "sku"],
    )


def downgrade() -> None:
    """Drop the inventory_items table if it exists."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "inventory_items" not in inspector.get_table_names():
        return

    op.drop_constraint("uq_inventory_org_sku", "inventory_items", type_="unique")
    op.drop_index("ix_inventory_org_id", table_name="inventory_items")
    op.drop_table("inventory_items")
