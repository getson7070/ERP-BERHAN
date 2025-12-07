"""
Add activity events, employee scorecards, and recommendations tables.

Revision ID: c8b3f8c4b8d1
Revises: 1e1f4c1d5cba
Create Date: 2025-02-24 00:00:00.000000
"""
from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "c8b3f8c4b8d1"
down_revision = "1e1f4c1d5cba"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activity_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("actor_type", sa.String(length=32), nullable=False, server_default="user"),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=True, index=True),
        sa.Column("entity_id", sa.Integer(), nullable=True, index=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="info"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
    )
    op.create_index(
        "ix_activity_events_org_action", "activity_events", ["org_id", "action"]
    )
    op.create_index(
        "ix_activity_events_actor", "activity_events", ["actor_user_id", "org_id"]
    )
    op.create_index(
        "ix_activity_events_entity", "activity_events", ["entity_type", "entity_id"]
    )

    op.create_table(
        "employee_scorecards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("sales_total", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("orders_closed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("maintenance_closed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overdue_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conversion_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("complaints", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("performance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("highlights", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.UniqueConstraint("org_id", "user_id", "period_start", name="uq_scorecards_period"),
    )
    op.create_index("ix_employee_scorecards_user", "employee_scorecards", ["user_id"])
    op.create_index(
        "ix_employee_scorecards_period",
        "employee_scorecards",
        ["period_start", "org_id"],
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="info"),
        sa.Column("created_for_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("source_period", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
    )
    op.create_index("ix_recommendations_status", "recommendations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_recommendations_status", table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_index("ix_employee_scorecards_period", table_name="employee_scorecards")
    op.drop_index("ix_employee_scorecards_user", table_name="employee_scorecards")
    op.drop_table("employee_scorecards")
    op.drop_index("ix_activity_events_entity", table_name="activity_events")
    op.drop_index("ix_activity_events_actor", table_name="activity_events")
    op.drop_index("ix_activity_events_org_action", table_name="activity_events")
    op.drop_table("activity_events")

