"""Add marketing campaigns, geofences, and consent tables."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d7e2c1d4e0fb"
down_revision = "c5ae18d6c3f1"
branch_labels = None
depends_on = None


def upgrade():
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

    op.create_table(
        "marketing_segments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("marketing_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("rules_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_marketing_segments_org", "marketing_segments", ["org_id"])
    op.create_index("ix_marketing_segments_campaign", "marketing_segments", ["campaign_id"])

    op.create_table(
        "marketing_consents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("marketing_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("location_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("consent_source", sa.String(length=64), nullable=True),
        sa.Column("consent_version", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_marketing_consents_subject", "marketing_consents", ["subject_id"])

    op.create_table(
        "marketing_ab_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("marketing_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False, server_default="50.00"),
        sa.Column("template_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_marketing_ab_variants_org", "marketing_ab_variants", ["org_id"])
    op.create_index("ix_marketing_ab_variants_campaign", "marketing_ab_variants", ["campaign_id"])

    op.create_table(
        "marketing_geofences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("marketing_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("center_lat", sa.Numeric(10, 6), nullable=False),
        sa.Column("center_lng", sa.Numeric(10, 6), nullable=False),
        sa.Column("radius_meters", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("action_type", sa.String(length=32), nullable=False, server_default="notify"),
        sa.Column("action_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_marketing_geofences_org", "marketing_geofences", ["org_id"])
    op.create_index("ix_marketing_geofences_campaign", "marketing_geofences", ["campaign_id"])

    # marketing_events was referenced as legacy in older chains but never created in the clean chain.
    # For fresh installs, create it here; for existing DBs, extend it idempotently.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "marketing_events" not in tables:
        op.create_table(
            "marketing_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False),
            sa.Column("campaign_id", sa.Integer(), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=True),
            sa.Column("event_type", sa.String(length=64), nullable=False, server_default="workshop"),
            sa.Column("venue", sa.String(length=255), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=True, server_default="planned"),
            sa.Column("subject_type", sa.String(length=32), nullable=True),
            sa.Column("subject_id", sa.Integer(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

        op.create_index("ix_marketing_events_campaign", "marketing_events", ["campaign_id"])
        op.create_index("ix_marketing_events_type", "marketing_events", ["event_type"])
        op.create_index("ix_marketing_events_org", "marketing_events", ["org_id"])
        op.create_index("ix_marketing_events_subject", "marketing_events", ["subject_id"])

        op.create_foreign_key(
            "fk_marketing_events_campaign",
            "marketing_events",
            "marketing_campaigns",
            ["campaign_id"],
            ["id"],
            ondelete="CASCADE",
        )
    else:
        cols = {c["name"] for c in inspector.get_columns("marketing_events")}
        if "campaign_id" not in cols:
            op.add_column("marketing_events", sa.Column("campaign_id", sa.Integer(), nullable=True))
        if "subject_type" not in cols:
            op.add_column("marketing_events", sa.Column("subject_type", sa.String(length=32), nullable=True))
        if "subject_id" not in cols:
            op.add_column("marketing_events", sa.Column("subject_id", sa.Integer(), nullable=True))
        if "metadata_json" not in cols:
            op.add_column(
                "marketing_events",
                sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            )

        # indexes + FK (create only if missing)
        existing_idx = {ix["name"] for ix in inspector.get_indexes("marketing_events")}
        if "ix_marketing_events_campaign" not in existing_idx:
            op.create_index("ix_marketing_events_campaign", "marketing_events", ["campaign_id"])
        if "ix_marketing_events_type" not in existing_idx:
            op.create_index("ix_marketing_events_type", "marketing_events", ["event_type"])
        if "ix_marketing_events_org" not in existing_idx:
            op.create_index("ix_marketing_events_org", "marketing_events", ["org_id"])
        if "ix_marketing_events_subject" not in existing_idx:
            op.create_index("ix_marketing_events_subject", "marketing_events", ["subject_id"])

        fk_names = {fk["name"] for fk in inspector.get_foreign_keys("marketing_events") if fk.get("name")}
        if "fk_marketing_events_campaign" not in fk_names:
            op.create_foreign_key(
                "fk_marketing_events_campaign",
                "marketing_events",
                "marketing_campaigns",
                ["campaign_id"],
                ["id"],
                ondelete="CASCADE",
            )



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
