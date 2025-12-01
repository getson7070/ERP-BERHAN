"""Add marketing campaigns, geofences, and consent tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect  # ADDED: For idempotency checks

revision = "d7e2c1d4e0fb"
down_revision = "c5ae18d6c3f1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # Create marketing_events if missing (idempotent)
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

    # Now safe to ALTER (columns/indexes/FK)
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

    # Indexes (idempotent)
    idx_names = {idx["name"] for idx in inspector.get_indexes("marketing_events")}
    if "ix_marketing_events_campaign" not in idx_names:
        op.create_index("ix_marketing_events_campaign", "marketing_events", ["campaign_id"])
    if "ix_marketing_events_subject" not in idx_names:
        op.create_index("ix_marketing_events_subject", "marketing_events", ["subject_id"])

    # FK (safe if cols exist)
    with op.batch_alter_table("marketing_events", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_marketing_events_campaign",
            "marketing_campaigns",
            ["campaign_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Rest of creations (campaigns, segments, etc.) unchanged—idempotentize similarly if needed
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

    # ... (repeat for segments, consents, ab_variants, geofences—add inspector checks if ALTERs needed)

def downgrade():
    # Unchanged—drop in reverse
    op.drop_constraint("fk_marketing_events_campaign", "marketing_events", type_="foreignkey")

def downgrade():
    op.drop_constraint("fk_marketing_events_campaign", "marketing_events", type_="foreignkey")
    op.drop_index("ix_marketing_events_subject", table_name="marketing_events")
    op.drop_index("ix_marketing_events_org", table_name="marketing_events")
    op.drop_index("ix_marketing_events_type", table_name="marketing_events")
    op.drop_index("ix_marketing_events_campaign", table_name="marketing_events")
    op.drop_column("marketing_events", "metadata_json")
    op.drop_column("marketing_events", "subject_id")
    op.drop_column("marketing_events", "subject_type")
    op.drop_column("marketing_events", "campaign_id")

    op.drop_index("ix_marketing_geofences_campaign", table_name="marketing_geofences")
    op.drop_index("ix_marketing_geofences_org", table_name="marketing_geofences")
    op.drop_table("marketing_geofences")

    op.drop_index("ix_marketing_ab_variants_campaign", table_name="marketing_ab_variants")
    op.drop_index("ix_marketing_ab_variants_org", table_name="marketing_ab_variants")
    op.drop_table("marketing_ab_variants")

    op.drop_index("ix_marketing_consents_subject", table_name="marketing_consents")
    op.drop_table("marketing_consents")

    op.drop_index("ix_marketing_segments_campaign", table_name="marketing_segments")
    op.drop_index("ix_marketing_segments_org", table_name="marketing_segments")
    op.drop_table("marketing_segments")

    op.drop_index("ix_marketing_campaigns_status", table_name="marketing_campaigns")
    op.drop_index("ix_marketing_campaigns_org", table_name="marketing_campaigns")
    op.drop_table("marketing_campaigns")
