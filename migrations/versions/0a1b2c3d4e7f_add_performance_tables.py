"""Add KPI registry, scorecards, evaluations, and ML suggestions."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0a1b2c3d4e7f"
down_revision = "f4a5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "kpi_registry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("kpi_key", sa.String(length=128), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("weight", sa.Numeric(6, 4), nullable=False, server_default="1.0"),
        sa.Column("direction", sa.String(length=16), nullable=False, server_default="higher_better"),
        sa.Column("min_score", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("max_score", sa.Numeric(6, 3), nullable=False, server_default="100"),
        sa.Column("privacy_class", sa.String(length=32), nullable=False, server_default="internal"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.UniqueConstraint("org_id", "kpi_key", name="uq_kpi_key"),
    )

    op.create_table(
        "scorecard_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False, index=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )

    op.create_table(
        "scorecard_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("scorecard_templates.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("kpi_key", sa.String(length=128), nullable=False, index=True),
        sa.Column("weight_override", sa.Numeric(6, 4), nullable=True),
        sa.Column("target_override", sa.Numeric(18, 4), nullable=True),
        sa.UniqueConstraint("org_id", "template_id", "kpi_key", name="uq_scorecard_kpi"),
    )

    op.create_table(
        "review_cycles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False, index=True),
        sa.Column("end_date", sa.Date(), nullable=False, index=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "performance_evaluations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("cycle_id", sa.Integer(), sa.ForeignKey("review_cycles.id", ondelete=None), nullable=False, index=True),
        sa.Column("subject_type", sa.String(length=32), nullable=False, index=True),
        sa.Column("subject_id", sa.Integer(), nullable=False, index=True),
        sa.Column("scorecard_template_id", sa.Integer(), nullable=True, index=True),
        sa.Column("total_score", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("breakdown_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="computed", index=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.UniqueConstraint("org_id", "cycle_id", "subject_type", "subject_id", name="uq_eval_subject_cycle"),
    )

    op.create_table(
        "feedback_360",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("evaluation_id", sa.BigInteger(), sa.ForeignKey("performance_evaluations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("giver_type", sa.String(length=32), nullable=False, server_default="user"),
        sa.Column("giver_id", sa.Integer(), nullable=False, index=True),
        sa.Column("rating", sa.Numeric(4, 2), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("dimension", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "ml_suggestions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("cycle_id", sa.Integer(), nullable=False, index=True),
        sa.Column("subject_type", sa.String(length=32), nullable=False, index=True),
        sa.Column("subject_id", sa.Integer(), nullable=False, index=True),
        sa.Column("suggestion_type", sa.String(length=64), nullable=False, index=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0.5"),
        sa.Column("reason_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("ml_suggestions")
    op.drop_table("feedback_360")
    op.drop_table("performance_evaluations")
    op.drop_table("review_cycles")
    op.drop_table("scorecard_items")
    op.drop_table("scorecard_templates")
    op.drop_table("kpi_registry")
