"""Add procurement tickets, milestones, and landed cost linkage.

Revision ID: 1e1f4c1d5cba
Revises: 7c8b0d3f3d2a
Create Date: 2025-02-24 00:00:00.000000
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "1e1f4c1d5cba"
down_revision = "7c8b0d3f3d2a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "procurement_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False, index=True),
        sa.Column("purchase_order_id", sa.Integer(), sa.ForeignKey("purchase_orders.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="submitted"),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="normal"),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("breached_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalation_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assigned_to_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_reason", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_reason", sa.Text(), nullable=True),
        sa.Column("landed_cost_total", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("landed_cost_posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
    )
    op.create_index("ix_procurement_tickets_org_status", "procurement_tickets", ["organization_id", "status"])
    op.create_index("ix_procurement_tickets_assigned", "procurement_tickets", ["assigned_to_id"])

    op.create_table(
        "procurement_milestones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False, index=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("procurement_tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("expected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
    )
    op.create_index(
        "ix_procurement_milestones_ticket",
        "procurement_milestones",
        ["ticket_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_procurement_milestones_ticket", table_name="procurement_milestones")
    op.drop_table("procurement_milestones")
    op.drop_index("ix_procurement_tickets_assigned", table_name="procurement_tickets")
    op.drop_index("ix_procurement_tickets_org_status", table_name="procurement_tickets")
    op.drop_table("procurement_tickets")
