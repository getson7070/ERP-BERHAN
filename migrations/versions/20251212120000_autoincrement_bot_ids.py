"""Ensure bot tables use auto-incrementing primary keys.

Revision ID: 20251212120000
Revises: 20251212100000
Create Date: 2025-12-12 12:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251212120000"
down_revision = "20251212100000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind else ""

    if dialect == "sqlite":
        # SQLite implicitly auto-increments INTEGER PRIMARY KEY columns; nothing to
        # do beyond keeping the model definition aligned for future creates.
        return

    # Postgres path: align sequences/defaults for bot idempotency + state tables.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'bot_idempotency_keys_id_seq') THEN
                CREATE SEQUENCE bot_idempotency_keys_id_seq;
            END IF;
            ALTER TABLE bot_idempotency_keys ALTER COLUMN id SET DEFAULT nextval('bot_idempotency_keys_id_seq');
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'telegram_conversation_state_id_seq') THEN
                CREATE SEQUENCE telegram_conversation_state_id_seq;
            END IF;
            ALTER TABLE telegram_conversation_state ALTER COLUMN id SET DEFAULT nextval('telegram_conversation_state_id_seq');
        END$$;
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind else ""

    if dialect == "sqlite":
        return

    op.execute("ALTER TABLE bot_idempotency_keys ALTER COLUMN id DROP DEFAULT;")
    op.execute("ALTER TABLE telegram_conversation_state ALTER COLUMN id DROP DEFAULT;")

    op.execute("DROP SEQUENCE IF EXISTS bot_idempotency_keys_id_seq;")
    op.execute("DROP SEQUENCE IF EXISTS telegram_conversation_state_id_seq;")
