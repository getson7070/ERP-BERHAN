"""add sku field to inventory_items

Revision ID: c3d4e5f6g7h
Revises: 7b8c9d0e1f2
Create Date: 2025-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c3d4e5f6g7h"
down_revision = "7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    cols = [
        row[1] for row in conn.execute(sa.text('PRAGMA table_info("inventory_items")'))
    ]
    if "sku" not in cols:
        op.add_column(
            "inventory_items", sa.Column("sku", sa.String(length=64), nullable=False)
        )
        op.create_index(
            "ix_inventory_items_sku", "inventory_items", ["sku"], unique=True
        )


def downgrade():
    op.drop_index("ix_inventory_items_sku", table_name="inventory_items")
    op.drop_column("inventory_items", "sku")
