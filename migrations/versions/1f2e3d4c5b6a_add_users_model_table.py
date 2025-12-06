"""Add users model table.

This creates the `users` table that the rest of the system expects.
It is written to be idempotent: if the table already exists, the
migration becomes a no-op. This protects against historic partial runs.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# Alembic revision identifiers.
revision = "1f2e3d4c5b6a"
down_revision = "ce91d3657d20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users table if it does not already exist."""
    bind = op.get_bind()
    insp = inspect(bind)

    # If the table is already there (from previous experiments), skip.
    existing_tables = set(insp.get_table_names())
    if "users" in existing_tables:
        return

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id"),
            nullable=True,
        ),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column(
            "is_superuser",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_staff",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )

    # Useful index for login/auth.
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    """Drop users table (reverse of upgrade)."""
    # Drop index first (safer when downgrading).
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
