"""create users table with idempotent guards"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20241007_0001"
down_revision = None
branch_labels = None
depends_on = None


def _inspector():
    return inspect(op.get_bind())


def _has_table(name: str) -> bool:
    try:
        return _inspector().has_table(name)
    except Exception:
        return False


def _has_index(table: str, index_name: str) -> bool:
    try:
        return any(idx["name"] == index_name for idx in _inspector().get_indexes(table))
    except Exception:
        return False


def upgrade() -> None:
    if not _has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    if not _has_index("users", "ix_users_email"):
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if not _has_index("users", "ix_users_role"):
        op.create_index("ix_users_role", "users", ["role"], unique=False)


def downgrade() -> None:
    if _has_index("users", "ix_users_role"):
        op.drop_index("ix_users_role", table_name="users")

    if _has_index("users", "ix_users_email"):
        op.drop_index("ix_users_email", table_name="users")

    if _has_table("users"):
        op.drop_table("users")
