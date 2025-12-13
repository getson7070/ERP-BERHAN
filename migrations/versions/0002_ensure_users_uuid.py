"""Ensure users.uuid exists (and is backfilled).

Revision ID: 0002_ensure_users_uuid
Revises: 20251212100000
Create Date: 2025-12-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_ensure_users_uuid"
down_revision = "20251212100000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # Add column if missing
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='users'
                  AND column_name='uuid'
            ) THEN
                ALTER TABLE public.users ADD COLUMN uuid varchar(36);
            END IF;
        END$$;
        """
    )

    # Backfill
    op.execute("UPDATE public.users SET uuid = gen_random_uuid()::text WHERE uuid IS NULL;")

    # Enforce not null
    op.execute("ALTER TABLE public.users ALTER COLUMN uuid SET NOT NULL;")

    # Unique index
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_uuid ON public.users (uuid);")


def downgrade() -> None:
    # Keep downgrade conservative
    op.execute("DROP INDEX IF EXISTS ix_users_uuid;")
    op.execute("ALTER TABLE public.users DROP COLUMN IF EXISTS uuid;")
