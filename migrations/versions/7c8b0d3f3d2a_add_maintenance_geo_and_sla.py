"""Add geo capture and SLA tracking to maintenance work orders.

Revision ID: 7c8b0d3f3d2a
Revises: 3f6bde5b7c29
Create Date: 2025-02-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7c8b0d3f3d2a"
down_revision = "3f6bde5b7c29"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "maintenance_work_orders",
        sa.Column("request_lat", sa.Float(), nullable=True),
    )
    op.add_column(
        "maintenance_work_orders",
        sa.Column("request_lng", sa.Float(), nullable=True),
    )
    op.add_column(
        "maintenance_work_orders",
        sa.Column("request_location_label", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "maintenance_work_orders",
        sa.Column("start_lat", sa.Float(), nullable=True),
    )
    op.add_column(
        "maintenance_work_orders",
        sa.Column("start_lng", sa.Float(), nullable=True),
    )
    op.add_column(
        "maintenance_work_orders",
        sa.Column("last_check_in_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "maintenance_work_orders",
        sa.Column(
            "sla_status",
            sa.String(length=32),
            nullable=False,
            server_default="ok",
        ),
    )

    op.add_column(
        "maintenance_events",
        sa.Column("geo_lat", sa.Float(), nullable=True),
    )
    op.add_column(
        "maintenance_events",
        sa.Column("geo_lng", sa.Float(), nullable=True),
    )

    op.add_column(
        "maintenance_escalation_events",
        sa.Column("note", sa.Text(), nullable=True),
    )

    op.create_index(
        "ix_maintenance_work_orders_sla_status",
        "maintenance_work_orders",
        ["sla_status"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_work_orders_due_date",
        "maintenance_work_orders",
        ["due_date"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_maintenance_work_orders_due_date",
        table_name="maintenance_work_orders",
    )
    op.drop_index(
        "ix_maintenance_work_orders_sla_status",
        table_name="maintenance_work_orders",
    )

    op.drop_column("maintenance_escalation_events", "note")

    op.drop_column("maintenance_events", "geo_lng")
    op.drop_column("maintenance_events", "geo_lat")

    op.drop_column("maintenance_work_orders", "sla_status")
    op.drop_column("maintenance_work_orders", "last_check_in_at")
    op.drop_column("maintenance_work_orders", "start_lng")
    op.drop_column("maintenance_work_orders", "start_lat")
    op.drop_column("maintenance_work_orders", "request_location_label")
    op.drop_column("maintenance_work_orders", "request_lng")
    op.drop_column("maintenance_work_orders", "request_lat")
