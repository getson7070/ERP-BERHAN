"""Add Telegram conversation state and bot job context."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2c3d4e5f6780"
down_revision = "15c2d3e4f5ab"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bot_job_outbox",
        sa.Column(
            "context_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    op.create_table(
        "telegram_conversation_state",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("bot_name", sa.String(length=64), nullable=False, index=True),
        sa.Column("chat_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("state_key", sa.String(length=64), nullable=False, index=True),
        sa.Column("data_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("org_id", "bot_name", "chat_id", name="uq_tg_state"),
    )


def downgrade():
    op.drop_table("telegram_conversation_state")
    op.drop_column("bot_job_outbox", "context_json")
