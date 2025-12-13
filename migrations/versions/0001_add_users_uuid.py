"""Add UUID column to users table (safe for fresh or legacy databases).

Revision ID: 0001_add_users_uuid
Revises: 739649794424
Create Date: 2025-12-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_add_users_uuid"
down_revision = "739649794424"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgcrypto provides gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("uuid", sa.String(length=36), nullable=True))

    # Backfill existing rows
    op.execute("UPDATE users SET uuid = gen_random_uuid()::text WHERE uuid IS NULL;")

    with op.batch_alter_table("users") as batch:
        batch.alter_column("uuid", nullable=False)

    op.create_index("ix_users_uuid", "users", ["uuid"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_uuid", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("uuid")
