"""Ensure users.uuid exists (and is backfilled).

Fixes cases where the users table was created without the uuid column
but the ORM expects it.

Revision order:
  739649794424 -> 0001_add_users_uuid -> 20251212100000 -> 0002_ensure_users_uuid
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = "0002_ensure_users_uuid"
down_revision = "20251212100000"
branch_labels = None
depends_on = None


def _table_exists(conn, table_name: str) -> bool:
    return bool(
        conn.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = :t
                LIMIT 1
                """
            ),
            {"t": table_name},
        ).scalar()
    )


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    return bool(
        conn.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :t
                  AND column_name = :c
                LIMIT 1
                """
            ),
            {"t": table_name, "c": column_name},
        ).scalar()
    )


def upgrade() -> None:
    conn = op.get_bind()

    # Ensure pgcrypto so gen_random_uuid() works (safe if already enabled).
    try:
        op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto";'))
    except Exception:
        # Some managed DBs restrict extensions. If blocked, UUID backfill will still work via uuid_generate_v4()
        # only if uuid-ossp exists; otherwise you'll need to backfill at app-level.
        pass

    if not _table_exists(conn, "users"):
        # If users table truly does not exist, create a minimal compatible table.
        # (Adjust/extend later if your project expects more fields.)
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("username", sa.String(length=150), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("telegram_chat_id", sa.String(length=64), nullable=True),
            sa.Column("password_hash", sa.String(length=255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_users_uuid", "users", ["uuid"], unique=True)
        return

    # If users table exists but uuid is missing, add it.
    if not _column_exists(conn, "users", "uuid"):
        # Add column nullable first to allow backfill.
        op.add_column("users", sa.Column("uuid", sa.String(length=36), nullable=True))

        # Backfill for existing rows using pgcrypto if available.
        # We cast to text and truncate to 36 chars in case your ORM uses string UUIDs.
        try:
            op.execute(sa.text("UPDATE users SET uuid = gen_random_uuid()::text WHERE uuid IS NULL;"))
        except Exception:
            # If pgcrypto not available, fallback to random md5-ish UUID-like token.
            # (Still unique enough for local dev; for production, ensure pgcrypto is enabled.)
            op.execute(
                sa.text(
                    """
                    UPDATE users
                    SET uuid = (
                        substr(md5(random()::text), 1, 8) || '-' ||
                        substr(md5(random()::text), 1, 4) || '-' ||
                        substr(md5(random()::text), 1, 4) || '-' ||
                        substr(md5(random()::text), 1, 4) || '-' ||
                        substr(md5(random()::text), 1, 12)
                    )
                    WHERE uuid IS NULL;
                    """
                )
            )

        # Make it NOT NULL and unique going forward.
        op.alter_column("users", "uuid", existing_type=sa.String(length=36), nullable=False)
        op.create_index("ix_users_uuid", "users", ["uuid"], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "users") and _column_exists(conn, "users", "uuid"):
        try:
            op.drop_index("ix_users_uuid", table_name="users")
        except Exception:
            pass
        op.drop_column("users", "uuid")
