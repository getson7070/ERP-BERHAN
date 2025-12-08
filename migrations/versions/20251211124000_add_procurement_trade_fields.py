"""add procurement trade fields

Revision ID: 20251211124000
Revises: 20251211123000
Create Date: 2025-12-11 12:40:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251211124000"
down_revision = "20251211123000"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("purchase_orders", sa.Column("pi_number", sa.String(length=64), nullable=True))
    op.add_column("purchase_orders", sa.Column("awb_number", sa.String(length=64), nullable=True))
    op.add_column("purchase_orders", sa.Column("hs_code", sa.String(length=64), nullable=True))
    op.add_column("purchase_orders", sa.Column("bank_name", sa.String(length=128), nullable=True))
    op.add_column("purchase_orders", sa.Column("customs_valuation", sa.Numeric(14, 2), nullable=True))
    op.add_column("purchase_orders", sa.Column("efda_reference", sa.String(length=64), nullable=True))
    op.create_index("ix_purchase_orders_pi_number", "purchase_orders", ["pi_number"], unique=False)
    op.create_index("ix_purchase_orders_awb_number", "purchase_orders", ["awb_number"], unique=False)
    op.create_index("ix_purchase_orders_hs_code", "purchase_orders", ["hs_code"], unique=False)
    op.create_index("ix_purchase_orders_efda_reference", "purchase_orders", ["efda_reference"], unique=False)


def downgrade():
    op.drop_index("ix_purchase_orders_efda_reference", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_hs_code", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_awb_number", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_pi_number", table_name="purchase_orders")
    op.drop_column("purchase_orders", "efda_reference")
    op.drop_column("purchase_orders", "customs_valuation")
    op.drop_column("purchase_orders", "bank_name")
    op.drop_column("purchase_orders", "hs_code")
    op.drop_column("purchase_orders", "awb_number")
    op.drop_column("purchase_orders", "pi_number")
