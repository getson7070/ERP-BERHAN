"""add lot, serial and potency tables

Revision ID: a1b2c3d4e5b
Revises: e6f7g8h9i0a
Create Date: 2024-05-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5b"
down_revision = "e6f7g8h9i0a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_lots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("inventory_items.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("lot_number", sa.String(length=64), nullable=False, unique=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expiry_date", sa.Date(), nullable=True),
    )
    op.create_index("ix_inventory_lots_expiry", "inventory_lots", ["expiry_date"])

    op.create_table(
        "inventory_serials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "lot_id",
            sa.Integer(),
            sa.ForeignKey("inventory_lots.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("serial_number", sa.String(length=128), nullable=False, unique=True),
    )

    op.create_table(
        "inventory_potencies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "lot_id",
            sa.Integer(),
            sa.ForeignKey("inventory_lots.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column(
            "tested_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("inventory_potencies")
    op.drop_table("inventory_serials")
    op.drop_index("ix_inventory_lots_expiry", table_name="inventory_lots")
    op.drop_table("inventory_lots")
