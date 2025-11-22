"""Add bot automation tables for commands, events, and outbox."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "15c2d3e4f5ab"
down_revision = "f4a5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bot_command_registry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("command", sa.String(length=64), nullable=False, index=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False, index=True),
        sa.Column("required_role", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("org_id", "command", name="uq_bot_command"),
    )

    op.create_table(
        "bot_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("bot_name", sa.String(length=64), nullable=False, index=True),
        sa.Column("event_type", sa.String(length=64), nullable=False, index=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False, server_default="user", index=True),
        sa.Column("actor_id", sa.Integer(), nullable=True, index=True),
        sa.Column("chat_id", sa.String(length=64), nullable=True, index=True),
        sa.Column("message_id", sa.String(length=64), nullable=True, index=True),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="info", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
    )

    op.create_table(
        "bot_job_outbox",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("bot_name", sa.String(length=64), nullable=False, index=True),
        sa.Column("chat_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("message_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parsed_intent", sa.String(length=64), nullable=True, index=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued", index=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "bot_idempotency_keys",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("bot_name", sa.String(length=64), nullable=False, index=True),
        sa.Column("chat_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("message_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("org_id", "bot_name", "chat_id", "message_id", name="uq_bot_idem"),
    )


def downgrade():
    op.drop_table("bot_idempotency_keys")
    op.drop_table("bot_job_outbox")
    op.drop_table("bot_events")
    op.drop_table("bot_command_registry")
