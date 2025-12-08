"""Add geo metadata to procurement milestones

Revision ID: 20251208153703
Revises: e1f9a41f2f2c
Create Date: 2025-12-08 15:37:03.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251208153703"
down_revision = "e1f9a41f2f2c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("procurement_milestones", sa.Column("geo_lat", sa.Float(), nullable=True))
    op.add_column("procurement_milestones", sa.Column("geo_lng", sa.Float(), nullable=True))
    op.add_column("procurement_milestones", sa.Column("geo_accuracy_m", sa.Float(), nullable=True))
    op.add_column("procurement_milestones", sa.Column("recorded_by_id", sa.Integer(), nullable=True))
    op.add_column(
        "procurement_milestones",
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(op.f("ix_procurement_milestones_recorded_by_id"), "procurement_milestones", ["recorded_by_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_procurement_milestones_recorded_by_id"), table_name="procurement_milestones")
    op.drop_column("procurement_milestones", "recorded_at")
    op.drop_column("procurement_milestones", "recorded_by_id")
    op.drop_column("procurement_milestones", "geo_accuracy_m")
    op.drop_column("procurement_milestones", "geo_lng")
    op.drop_column("procurement_milestones", "geo_lat")
