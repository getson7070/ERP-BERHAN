"""Add analytics registry, facts, dashboards, and lineage."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f4a5c6d7e8f9"
down_revision = ("e17e5f6c5f0b", "d7e2c1d4e0fb")
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analytics_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("key", sa.String(length=128), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("metric_type", sa.String(length=32), nullable=False, server_default="gauge"),
        sa.Column("privacy_class", sa.String(length=32), nullable=False, server_default="internal"),
        sa.Column("source_module", sa.String(length=64), nullable=False),
        sa.Column("source_query", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.UniqueConstraint("org_id", "key", name="uq_metric_key"),
    )

    op.create_table(
        "analytics_facts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("metric_key", sa.String(length=128), nullable=False, index=True),
        sa.Column("ts_date", sa.Date(), nullable=False, index=True),
        sa.Column("warehouse_id", sa.Integer(), nullable=True, index=True),
        sa.Column("region", sa.String(length=64), nullable=True, index=True),
        sa.Column("user_id", sa.Integer(), nullable=True, index=True),
        sa.Column("client_id", sa.Integer(), nullable=True, index=True),
        sa.Column("item_id", sa.Integer(), nullable=True, index=True),
        sa.Column("value", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "org_id",
            "metric_key",
            "ts_date",
            "warehouse_id",
            "region",
            "user_id",
            "client_id",
            "item_id",
            name="uq_fact_grain",
        ),
    )

    op.create_table(
        "analytics_dashboards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("for_role", sa.String(length=64), nullable=True, index=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )

    op.create_table(
        "analytics_widgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("dashboard_id", sa.Integer(), sa.ForeignKey("analytics_dashboards.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("metric_key", sa.String(length=128), nullable=False, index=True),
        sa.Column("chart_type", sa.String(length=32), nullable=False, server_default="line"),
        sa.Column("config_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "analytics_lineage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("metric_key", sa.String(length=128), nullable=False, index=True),
        sa.Column("upstream_tables", sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("transformation", sa.Text(), nullable=True),
        sa.Column("downstream_usage", sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("privacy_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW bi_daily_metrics AS
        SELECT
            org_id,
            metric_key,
            ts_date,
            warehouse_id,
            region,
            user_id,
            client_id,
            item_id,
            value
        FROM analytics_facts;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW bi_metrics_registry AS
        SELECT
            org_id,
            key AS metric_key,
            name,
            unit,
            metric_type,
            privacy_class,
            source_module
        FROM analytics_metrics;
        """
    )


def downgrade():
    op.execute("DROP VIEW IF EXISTS bi_metrics_registry")
    op.execute("DROP VIEW IF EXISTS bi_daily_metrics")
    op.drop_table("analytics_lineage")
    op.drop_table("analytics_widgets")
    op.drop_table("analytics_dashboards")
    op.drop_table("analytics_facts")
    op.drop_table("analytics_metrics")
