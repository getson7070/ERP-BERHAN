"""Add UUID column to users table.

This migration aligns the database with the current User model by
adding a UUID column with a server default and a unique constraint.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision = "0001_add_users_uuid"
down_revision = "739649794424"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgcrypto is available for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # Add the uuid column with default
    op.add_column(
        "users",
        sa.Column(
            "uuid",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )

    # Make uuid unique for lookups and external references
    op.create_unique_constraint(
        "uq_users_uuid",
        "users",
        ["uuid"],
    )


def downgrade() -> None:
    # Drop the unique constraint first, then the column
    op.drop_constraint("uq_users_uuid", "users", type_="unique")
    op.drop_column("users", "uuid")
