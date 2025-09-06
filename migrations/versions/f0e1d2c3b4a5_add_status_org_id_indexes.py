"""add indexes on status and org_id"""

from alembic import op

revision = "f0e1d2c3b4a5"
down_revision = "b2c3d4e5f6g"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_orders_status_org_id", "orders", ["status", "org_id"])
    op.create_index("ix_maintenance_status_org_id", "maintenance", ["status", "org_id"])
    op.create_index("ix_tenders_status_org_id", "tenders", ["status", "org_id"])


def downgrade() -> None:
    op.drop_index("ix_orders_status_org_id", table_name="orders")
    op.drop_index("ix_maintenance_status_org_id", table_name="maintenance")
    op.drop_index("ix_tenders_status_org_id", table_name="tenders")
