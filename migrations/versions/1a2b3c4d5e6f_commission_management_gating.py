"""Commission approval gating and block reasons for orders

Revision ID: 1a2b3c4d5e6f
Revises: e1f9a41f2f2c
Create Date: 2025-11-09 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "1a2b3c4d5e6f"
down_revision = "e1f9a41f2f2c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("orders"):
        return

    columns = {col["name"] for col in insp.get_columns("orders")}

    if "commission_approved_by_management" not in columns:
        op.add_column(
            "orders",
            sa.Column(
                "commission_approved_by_management",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )
    if "commission_block_reason" not in columns:
        op.add_column(
            "orders",
            sa.Column("commission_block_reason", sa.String(length=255), nullable=True),
        )

    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "commission_approved_by_management", server_default=None
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("orders"):
        return

    columns = {col["name"] for col in insp.get_columns("orders")}

    if "commission_block_reason" in columns:
        op.drop_column("orders", "commission_block_reason")
    if "commission_approved_by_management" in columns:
        op.drop_column("orders", "commission_approved_by_management")
