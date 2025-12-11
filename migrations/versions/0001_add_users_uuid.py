"""Add UUID column to users table (safe for fresh or legacy databases).

This migration is written to be idempotent and defensive:

- If the "users" table does NOT exist yet, it does nothing (no error).
  In those environments, the users table is expected to be created by
  other schema/bootstrap logic (e.g. SQLAlchemy `create_all` or a
  separate initial migration) and should already include the `uuid`
  column in its model definition.

- If the "users" table exists but already has a "uuid" column,
  it also does nothing.

- Otherwise, it adds a NOT NULL UUID column with a server default
  of gen_random_uuid(), then drops the default so future writes can
  rely on application-layer defaults if desired.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision = "0001_add_users_uuid"
down_revision = "739649794424"
branch_labels = None
depends_on = None


def _has_users_table(inspector: sa.engine.reflection.Inspector) -> bool:
    return inspector.has_table("users")


def _has_uuid_column(inspector: sa.engine.reflection.Inspector) -> bool:
    cols = inspector.get_columns("users")
    return any(col["name"] == "uuid" for col in cols)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # If there is no "users" table yet, we cannot ALTER it – bail out quietly.
    if not _has_users_table(inspector):
        # This environment likely relies on a later full-schema migration or
        # SQLAlchemy `create_all` that already includes the uuid column.
        return

    # If the "uuid" column is already present, do nothing.
    if _has_uuid_column(inspector):
        return

    # Add UUID column with a server default so existing rows get populated.
    op.add_column(
        "users",
        sa.Column(
            "uuid",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )

    # Optional: drop the server default so application code can control it.
    op.alter_column("users", "uuid", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_users_table(inspector):
        return

    if not _has_uuid_column(inspector):
        return

    op.drop_column("users", "uuid")
