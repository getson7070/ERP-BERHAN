"""Add UUID column to users table (safe for fresh or legacy databases).

This migration is intentionally defensive:

- If the `users` table does not exist yet, it exits cleanly.
- If the `uuid` column already exists, it exits cleanly.
- Otherwise, it adds a NOT NULL UUID column with a default of gen_random_uuid(),
  backfills, adds a unique constraint, then drops the default so future writes can
  rely on application-level generation if desired.

IMPORTANT: gen_random_uuid() requires the pgcrypto extension.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0001_add_users_uuid"
down_revision = None
branch_labels = None
depends_on = None


def _has_users_table(inspector) -> bool:
    try:
        return "users" in inspector.get_table_names()
    except Exception:
        return False


def _has_uuid_column(inspector) -> bool:
    try:
        cols = inspector.get_columns("users")
        return any((c.get("name") or "").lower() == "uuid" for c in cols)
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()

    # Ensure pgcrypto is available for gen_random_uuid() on fresh Postgres instances
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    except Exception:
        # Some managed DBs restrict extension creation; if blocked, the migration will
        # fail later when gen_random_uuid() is called. This is still the safest default.
        pass

    inspector = inspect(bind)

    # If there is no "users" table yet, we cannot ALTER it – bail out quietly.
    if not _has_users_table(inspector):
        return

    # If the "uuid" column is already present, do nothing.
    if _has_uuid_column(inspector):
        return

    # Add uuid column with server default (requires pgcrypto)
    op.add_column(
        "users",
        sa.Column("uuid", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
    )

    # Backfill (defensive; for any rows where default did not apply)
    op.execute("UPDATE users SET uuid = gen_random_uuid() WHERE uuid IS NULL")

    # Enforce uniqueness
    op.create_unique_constraint("uq_users_uuid", "users", ["uuid"])

    # Drop server default (optional but recommended)
    op.alter_column("users", "uuid", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_users_table(inspector):
        return
    if not _has_uuid_column(inspector):
        return

    op.drop_constraint("uq_users_uuid", "users", type_="unique")
    op.drop_column("users", "uuid")
