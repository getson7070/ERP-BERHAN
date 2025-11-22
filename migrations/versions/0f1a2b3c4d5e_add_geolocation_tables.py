"""Add geolocation tracking tables."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0f1a2b3c4d5e"
down_revision = "f4a5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "geo_pings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("lat", sa.Numeric(10, 6), nullable=False),
        sa.Column("lng", sa.Numeric(10, 6), nullable=False),
        sa.Column("accuracy_m", sa.Integer(), nullable=True),
        sa.Column("speed_mps", sa.Numeric(10, 3), nullable=True),
        sa.Column("heading_deg", sa.Numeric(6, 2), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="app"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_geo_pings_org", "geo_pings", ["org_id"])
    op.create_index("ix_geo_pings_subject_type", "geo_pings", ["subject_type"])
    op.create_index("ix_geo_pings_subject_id", "geo_pings", ["subject_id"])
    op.create_index(
        "ix_geo_pings_subject_time",
        "geo_pings",
        ["org_id", "subject_type", "subject_id", "recorded_at"],
    )

    op.create_table(
        "geo_last_locations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("lat", sa.Numeric(10, 6), nullable=False),
        sa.Column("lng", sa.Numeric(10, 6), nullable=False),
        sa.Column("accuracy_m", sa.Integer(), nullable=True),
        sa.Column("speed_mps", sa.Numeric(10, 3), nullable=True),
        sa.Column("heading_deg", sa.Numeric(6, 2), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("org_id", "subject_type", "subject_id", name="uq_geo_last"),
    )
    op.create_index("ix_geo_last_org", "geo_last_locations", ["org_id"])
    op.create_index("ix_geo_last_subject_type", "geo_last_locations", ["subject_type"])
    op.create_index("ix_geo_last_subject_id", "geo_last_locations", ["subject_id"])

    op.create_table(
        "geo_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dest_lat", sa.Numeric(10, 6), nullable=True),
        sa.Column("dest_lng", sa.Numeric(10, 6), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_geo_assign_org", "geo_assignments", ["org_id"])
    op.create_index("ix_geo_assign_subject", "geo_assignments", ["subject_id"])
    op.create_index("ix_geo_assign_task", "geo_assignments", ["org_id", "task_type", "task_id"])
    op.create_index("ix_geo_assign_status", "geo_assignments", ["status"])

    op.create_table(
        "geo_route_cache",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("cache_key", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="internal"),
        sa.Column("route_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("eta_seconds", sa.Integer(), nullable=True),
        sa.Column("distance_meters", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("org_id", "cache_key", name="uq_route_cache"),
    )
    op.create_index("ix_geo_route_cache_org", "geo_route_cache", ["org_id"])
    op.create_index("ix_geo_route_cache_key", "geo_route_cache", ["cache_key"])


def downgrade():
    op.drop_index("ix_geo_route_cache_key", table_name="geo_route_cache")
    op.drop_index("ix_geo_route_cache_org", table_name="geo_route_cache")
    op.drop_table("geo_route_cache")

    op.drop_index("ix_geo_assign_status", table_name="geo_assignments")
    op.drop_index("ix_geo_assign_task", table_name="geo_assignments")
    op.drop_index("ix_geo_assign_subject", table_name="geo_assignments")
    op.drop_index("ix_geo_assign_org", table_name="geo_assignments")
    op.drop_table("geo_assignments")

    op.drop_index("ix_geo_last_subject_id", table_name="geo_last_locations")
    op.drop_index("ix_geo_last_subject_type", table_name="geo_last_locations")
    op.drop_index("ix_geo_last_org", table_name="geo_last_locations")
    op.drop_table("geo_last_locations")

    op.drop_index("ix_geo_pings_subject_time", table_name="geo_pings")
    op.drop_index("ix_geo_pings_subject_id", table_name="geo_pings")
    op.drop_index("ix_geo_pings_subject_type", table_name="geo_pings")
    op.drop_index("ix_geo_pings_org", table_name="geo_pings")
    op.drop_table("geo_pings")
