"""Add geo metadata to orders for auditability

Revision ID: 20251209120000
Revises: 20251208153703
Create Date: 2025-12-09 12:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251209120000"
down_revision = "20251208153703"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("geo_lat", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("geo_lng", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("geo_accuracy_m", sa.Float(), nullable=True))
    op.add_column("orders", sa.Column("geo_recorded_by_id", sa.Integer(), nullable=True))
    op.add_column(
        "orders",
        sa.Column("geo_recorded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_orders_geo_recorded_by_id"), "orders", ["geo_recorded_by_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_geo_recorded_by_id"), table_name="orders")
    op.drop_column("orders", "geo_recorded_at")
    op.drop_column("orders", "geo_recorded_by_id")
    op.drop_column("orders", "geo_accuracy_m")
    op.drop_column("orders", "geo_lng")
    op.drop_column("orders", "geo_lat")
