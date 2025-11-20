"""Add immutable audit spine with searchable metadata and encryption columns."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b4d7e6f9c0a1"
down_revision = "a12b34c56d78"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "audit_logs",
        sa.Column("actor_type", sa.String(length=32), nullable=False, server_default="user"),
    )
    op.add_column("audit_logs", sa.Column("actor_id", sa.Integer(), nullable=True))
    op.add_column("audit_logs", sa.Column("ip_address", sa.String(length=64), nullable=True))
    op.add_column("audit_logs", sa.Column("user_agent", sa.String(length=255), nullable=True))
    op.add_column("audit_logs", sa.Column("request_id", sa.String(length=64), nullable=True))
    op.add_column(
        "audit_logs",
        sa.Column("module", sa.String(length=64), nullable=False, server_default="general"),
    )
    op.add_column(
        "audit_logs",
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="info"),
    )
    op.add_column("audit_logs", sa.Column("entity_type", sa.String(length=64), nullable=True))
    op.add_column("audit_logs", sa.Column("entity_id", sa.Integer(), nullable=True))
    op.add_column(
        "audit_logs",
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column("audit_logs", sa.Column("payload_encrypted", sa.JSON(), nullable=True))

    op.create_index(
        "ix_audit_org_mod_action_time",
        "audit_logs",
        ["org_id", "module", "action", "created_at"],
        unique=False,
    )

    op.execute("UPDATE audit_logs SET actor_id = COALESCE(actor_id, user_id)")
    op.execute("UPDATE audit_logs SET module = COALESCE(module, action)")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_logs_immutable()
        RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'audit_logs is append-only. UPDATE/DELETE not allowed.';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_immutable ON audit_logs")
    op.execute(
        """
        CREATE TRIGGER trg_audit_logs_immutable
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION audit_logs_immutable();
        """
    )


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_immutable ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS audit_logs_immutable")
    op.drop_index("ix_audit_org_mod_action_time", table_name="audit_logs")
    op.drop_column("audit_logs", "payload_encrypted")
    op.drop_column("audit_logs", "metadata_json")
    op.drop_column("audit_logs", "entity_id")
    op.drop_column("audit_logs", "entity_type")
    op.drop_column("audit_logs", "severity")
    op.drop_column("audit_logs", "module")
    op.drop_column("audit_logs", "request_id")
    op.drop_column("audit_logs", "user_agent")
    op.drop_column("audit_logs", "ip_address")
    op.drop_column("audit_logs", "actor_id")
    op.drop_column("audit_logs", "actor_type")
