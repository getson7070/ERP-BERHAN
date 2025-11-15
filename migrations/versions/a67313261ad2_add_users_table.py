"""add users / employees table (idempotent)

Revision ID: a67313261ad2
Revises: 59764003235d
Create Date: 2024-XX-XX

This revision used to unconditionally create the `employees` table.
That caused DuplicateTable errors when migrations were run more than once
or when the table already existed (e.g. after consolidation).

We now make it idempotent: if `employees` already exists, we skip creation.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "a67313261ad2"
down_revision = "59764003235d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = set(inspector.get_table_names())

    if "employees" in existing_tables:
        # Table is already present (possibly created by an earlier
        # consolidated migration or a prior run). Treat as already applied.
        return

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("role", sa.String(length=120)),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    # Be conservative on downgrade: only drop if it exists.
    bind = op.get_bind()
    inspector = inspect(bind)

    if "employees" in inspector.get_table_names():
        op.drop_table("employees")
