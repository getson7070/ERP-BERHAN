"""Add marketing campaigns, geofences, and consent tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "d7e2c1d4e0fb"
down_revision = "c5ae18d6c3f1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # Create marketing_campaigns first (dependency)
    if "marketing_campaigns" not in tables:
        op.create_table(
            "marketing_campaigns",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
            sa.Column("channel", sa.String(length=32), nullable=False, server_default="telegram"),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("budget", sa.Numeric(14, 2), nullable=True),
            sa.Column("currency", sa.String(length=8), nullable=False, server_default="ETB"),
            sa.Column("ab_test_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_marketing_campaigns_org", "marketing_campaigns", ["org_id"])
        op.create_index("ix_marketing_campaigns_status", "marketing_campaigns", ["status"])

    # Create marketing_events if missing
    if "marketing_events" not in tables:
        op.create_table(
            "marketing_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("event_type", sa.String(length=64), nullable=False, index=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("location_lat", sa.Numeric(10, 6), nullable=True),
            sa.Column("location_lng", sa.Numeric(10, 6), nullable=True),
            sa.Column("device_id", sa.String(length=128), nullable=True),
            sa.Column("session_id", sa.String(length=128), nullable=True),
            sa.Column("user_agent", sa.String(length=512), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_marketing_events_org", "marketing_events", ["org_id"])
        op.create_index("ix_marketing_events_type", "marketing_events", ["event_type"])

    # Safe ALTERs for marketing_events
    existing_cols = {col["name"] for col in inspector.get_columns("marketing_events")}
    if "campaign_id" not in existing_cols:
        op.add_column("marketing_events", sa.Column("campaign_id", sa.Integer(), nullable=True))
    if "subject_type" not in existing_cols:
        op.add_column("marketing_events", sa.Column("subject_type", sa.String(length=32), nullable=True))
    if "subject_id" not in existing_cols:
        op.add_column("marketing_events", sa.Column("subject_id", sa.Integer(), nullable=True))
    if "metadata_json" not in existing_cols:
        op.add_column(
            "marketing_events",
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        )

    # Safe indexes for marketing_events
    idx_names = {idx["name"] for idx in inspector.get_indexes("marketing_events")}
    if "ix_marketing_events_campaign" not in idx_names:
        op.create_index("ix_marketing_events_campaign", "marketing_events", ["campaign_id"])
    if "ix_marketing_events_subject" not in idx_names:
        op.create_index("ix_marketing_events_subject", "marketing_events", ["subject_id"])

    # Safe FK for marketing_events (campaigns exists)
    fk_names = {fk["name"] for fk in inspector.get_foreign_keys("marketing_events")}
    if "fk_marketing_events_campaign" not in fk_names:
        with op.batch_alter_table("marketing_events", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_marketing_events_campaign",
                "marketing_campaigns",
                ["campaign_id"],
                ["id"],
                ondelete="CASCADE",
            )

    # Create marketing_segments if missing
    if "marketing_segments" not in tables:
        op.create_table(
            "marketing_segments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False),
            sa.Column("campaign_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("criteria_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("percentage", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_marketing_segments_campaign", "marketing_segments", ["campaign_id"])
        op.create_index("ix_marketing_segments_org", "marketing_segments", ["org_id"])

    # Safe FK for marketing_segments
    fk_names = {fk["name"] for fk in inspector.get_foreign_keys("marketing_segments")}
    if "fk_marketing_segments_campaign" not in fk_names:
        with op.batch_alter_table("marketing_segments", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_marketing_segments_campaign",
                "marketing_campaigns",  # dest_table
                ["campaign_id"],  # source_cols
                ["id"],  # dest_cols
                ondelete="CASCADE",
            )

    # Create marketing_consents if missing
    if "marketing_consents" not in tables:
        op.create_table(
            "marketing_consents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("user_id", sa.Integer(), nullable=True, index=True),
            sa.Column("subject_type", sa.String(length=32), nullable=False),
            sa.Column("subject_id", sa.Integer(), nullable=False),
            sa.Column("consent_type", sa.String(length=64), nullable=False),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=512), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_marketing_consents_subject", "marketing_consents", ["subject_type", "subject_id"])
        op.create_index("ix_marketing_consents_org", "marketing_consents", ["org_id"])

    # Create marketing_ab_variants if missing
    if "marketing_ab_variants" not in tables:
        op.create_table(
            "marketing_ab_variants",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False),
            sa.Column("campaign_id", sa.Integer(), nullable=False),
            sa.Column("variant_name", sa.String(length=128), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_marketing_ab_variants_campaign", "marketing_ab_variants", ["campaign_id"])
        op.create_index("ix_marketing_ab_variants_org", "marketing_ab_variants", ["org_id"])

    # Safe FK for marketing_ab_variants
    fk_names = {fk["name"] for fk in inspector.get_foreign_keys("marketing_ab_variants")}
    if "fk_marketing_ab_variants_campaign" not in fk_names:
        with op.batch_alter_table("marketing_ab_variants", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_marketing_ab_variants_campaign",
                "marketing_campaigns",
                ["campaign_id"],
                ["id"],
                ondelete="CASCADE",
            )

    # Create marketing_geofences if missing
    if "marketing_geofences" not in tables:
        op.create_table(
            "marketing_geofences",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False),
            sa.Column("campaign_id", sa.Integer(), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("center_lat", sa.Numeric(10, 6), nullable=False),
            sa.Column("center_lng", sa.Numeric(10, 6), nullable=False),
            sa.Column("radius_meters", sa.Integer(), nullable=False),
            sa.Column("active_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("active_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("triggers", sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_marketing_geofences_campaign", "marketing_geofences", ["campaign_id"])
        op.create_index("ix_marketing_geofences_org", "marketing_geofences", ["org_id"])

    # Safe FK for marketing_geofences
    fk_names = {fk["name"] for fk in inspector.get_foreign_keys("marketing_geofences")}
    if "fk_marketing_geofences_campaign" not in fk_names:
        with op.batch_alter_table("marketing_geofences", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_marketing_geofences_campaign",
                "marketing_campaigns",
                ["campaign_id"],
                ["id"],
                ondelete="CASCADE",
            )


def downgrade():
    # Drop in reverse (FKs first)
    with op.batch_alter_table("marketing_geofences", schema=None) as batch_op:
        batch_op.drop_constraint("fk_marketing_geofences_campaign", type_="foreignkey")

    op.drop_index("ix_marketing_geofences_org", table_name="marketing_geofences")
    op.drop_index("ix_marketing_geofences_campaign", table_name="marketing_geofences")
    op.drop_table("marketing_geofences")

    with op.batch_alter_table("marketing_ab_variants", schema=None) as batch_op:
        batch_op.drop_constraint("fk_marketing_ab_variants_campaign", type_="foreignkey")

    op.drop_index("ix_marketing_ab_variants_org", table_name="marketing_ab_variants")
    op.drop_index("ix_marketing_ab_variants_campaign", table_name="marketing_ab_variants")
    op.drop_table("marketing_ab_variants")

    op.drop_index("ix_marketing_consents_org", table_name="marketing_consents")
    op.drop_index("ix_marketing_consents_subject", table_name="marketing_consents")
    op.drop_table("marketing_consents")

    with op.batch_alter_table("marketing_segments", schema=None) as batch_op:
        batch_op.drop_constraint("fk_marketing_segments_campaign", type_="foreignkey")

    op.drop_index("ix_marketing_segments_org", table_name="marketing_segments")
    op.drop_index("ix_marketing_segments_campaign", table_name="marketing_segments")
    op.drop_table("marketing_segments")

    with op.batch_alter_table("marketing_events", schema=None) as batch_op:
        batch_op.drop_constraint("fk_marketing_events_campaign", type_="foreignkey")

    op.drop_index("ix_marketing_events_subject", table_name="marketing_events")
    op.drop_index("ix_marketing_events_campaign", table_name="marketing_events")
    op.drop_index("ix_marketing_events_org", table_name="marketing_events")
    op.drop_index("ix_marketing_events_type", table_name="marketing_events")
    op.drop_column("marketing_events", "metadata_json")
    op.drop_column("marketing_events", "subject_id")
    op.drop_column("marketing_events", "subject_type")
    op.drop_column("marketing_events", "campaign_id")
    op.drop_table("marketing_events")

    op.drop_index("ix_marketing_campaigns_status", table_name="marketing_campaigns")
    op.drop_index("ix_marketing_campaigns_org", table_name="marketing_campaigns")
    op.drop_table("marketing_campaigns")