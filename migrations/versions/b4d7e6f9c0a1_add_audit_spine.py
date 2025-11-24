"""Add immutable audit spine with searchable metadata and encryption columns.

WHY THIS REVISION EXISTS
------------------------
Earlier revisions (e.g. 8f5c2e7d9a4b) referenced an audit log concept but on
a fresh database the `audit_logs` table may not exist at all, causing this
revision to fail when it tries to ALTER TABLE.

This revision is now self-bootstrapping and idempotent:

- If `audit_logs` does not exist, it is created with a complete, final schema.
- If it already exists, we only add the missing columns.

This keeps fresh installs working while remaining safe for existing databases.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b4d7e6f9c0a1"
down_revision = "a12b34c56d78"
branch_labels = None
depends_on = None


def _has_table(insp, name: str) -> bool:
    return insp.has_table(name)


def _has_col(insp, table: str, col: str) -> bool:
    return col in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # ------------------------------------------------------------------
    # 1) BOOTSTRAP audit_logs IF MISSING
    # ------------------------------------------------------------------
    if not _has_table(insp, "audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("scope", sa.String(length=64), nullable=True),
            sa.Column("severity", sa.String(length=32), nullable=True),

            # Who / what performed the action
            sa.Column(
                "actor_type",
                sa.String(length=32),
                nullable=False,
                server_default="user",
            ),
            sa.Column("actor_id", sa.String(length=64), nullable=True),

            # What resource the action touched
            sa.Column("resource_type", sa.String(length=64), nullable=True),
            sa.Column("resource_id", sa.String(length=64), nullable=True),

            # Request context
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=255), nullable=True),
            sa.Column("correlation_id", sa.String(length=64), nullable=True),

            # Business metadata / payload (searchable)
            sa.Column(
                "metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),

            # Cryptographic / tamper-evident chain
            sa.Column("hash_prev", sa.String(length=128), nullable=True),
            sa.Column("hash_curr", sa.String(length=128), nullable=True),
            sa.Column(
                "is_tampered",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),

            # Encryption support
            sa.Column("encryption_key_id", sa.String(length=64), nullable=True),
            sa.Column("ciphertext", sa.LargeBinary(), nullable=True),

            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

        op.create_index(
            "ix_audit_logs_org_created",
            "audit_logs",
            ["org_id", "created_at"],
        )
        op.create_index(
            "ix_audit_logs_event_created",
            "audit_logs",
            ["event_type", "created_at"],
        )
        op.create_index(
            "ix_audit_logs_resource",
            "audit_logs",
            ["resource_type", "resource_id"],
        )

        # Table is fully created; nothing else to extend.
        return

    # ------------------------------------------------------------------
    # 2) EXTEND EXISTING audit_logs SAFELY
    # ------------------------------------------------------------------

    # actor_type (this is where the original failure happened)
    if not _has_col(insp, "audit_logs", "actor_type"):
        op.add_column(
            "audit_logs",
            sa.Column(
                "actor_type",
                sa.String(length=32),
                nullable=False,
                server_default="user",
            ),
        )

    # actor_id
    if not _has_col(insp, "audit_logs", "actor_id"):
        op.add_column(
            "audit_logs",
            sa.Column("actor_id", sa.String(length=64), nullable=True),
        )

    # scope
    if not _has_col(insp, "audit_logs", "scope"):
        op.add_column(
            "audit_logs",
            sa.Column("scope", sa.String(length=64), nullable=True),
        )

    # severity
    if not _has_col(insp, "audit_logs", "severity"):
        op.add_column(
            "audit_logs",
            sa.Column("severity", sa.String(length=32), nullable=True),
        )

    # resource_type / resource_id
    if not _has_col(insp, "audit_logs", "resource_type"):
        op.add_column(
            "audit_logs",
            sa.Column("resource_type", sa.String(length=64), nullable=True),
        )
    if not _has_col(insp, "audit_logs", "resource_id"):
        op.add_column(
            "audit_logs",
            sa.Column("resource_id", sa.String(length=64), nullable=True),
        )

    # ip_address / user_agent / correlation_id
    if not _has_col(insp, "audit_logs", "ip_address"):
        op.add_column(
            "audit_logs",
            sa.Column("ip_address", sa.String(length=45), nullable=True),
        )
    if not _has_col(insp, "audit_logs", "user_agent"):
        op.add_column(
            "audit_logs",
            sa.Column("user_agent", sa.String(length=255), nullable=True),
        )
    if not _has_col(insp, "audit_logs", "correlation_id"):
        op.add_column(
            "audit_logs",
            sa.Column("correlation_id", sa.String(length=64), nullable=True),
        )

    # metadata JSONB
    if not _has_col(insp, "audit_logs", "metadata"):
        op.add_column(
            "audit_logs",
            sa.Column(
                "metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
        )

    # hash_prev / hash_curr / is_tampered
    if not _has_col(insp, "audit_logs", "hash_prev"):
        op.add_column(
            "audit_logs",
            sa.Column("hash_prev", sa.String(length=128), nullable=True),
        )
    if not _has_col(insp, "audit_logs", "hash_curr"):
        op.add_column(
            "audit_logs",
            sa.Column("hash_curr", sa.String(length=128), nullable=True),
        )
    if not _has_col(insp, "audit_logs", "is_tampered"):
        op.add_column(
            "audit_logs",
            sa.Column(
                "is_tampered",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )

    # encryption support
    if not _has_col(insp, "audit_logs", "encryption_key_id"):
        op.add_column(
            "audit_logs",
            sa.Column("encryption_key_id", sa.String(length=64), nullable=True),
        )
    if not _has_col(insp, "audit_logs", "ciphertext"):
        op.add_column(
            "audit_logs",
            sa.Column("ciphertext", sa.LargeBinary(), nullable=True),
        )

    # indexes (create only if missing)
    existing_indexes = {idx["name"] for idx in insp.get_indexes("audit_logs")}

    if "ix_audit_logs_org_created" not in existing_indexes:
        op.create_index(
            "ix_audit_logs_org_created",
            "audit_logs",
            ["org_id", "created_at"],
        )

    if "ix_audit_logs_event_created" not in existing_indexes:
        op.create_index(
            "ix_audit_logs_event_created",
            "audit_logs",
            ["event_type", "created_at"],
        )

    if "ix_audit_logs_resource" not in existing_indexes:
        op.create_index(
            "ix_audit_logs_resource",
            "audit_logs",
            ["resource_type", "resource_id"],
        )


def downgrade() -> None:
    # For simplicity and safety, if the table exists we drop it.
    # This avoids leaving behind a half-removed schema on downgrade.
    bind = op.get_bind()
    insp = inspect(bind)

    if _has_table(insp, "audit_logs"):
        op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
        op.drop_index("ix_audit_logs_event_created", table_name="audit_logs")
        op.drop_index("ix_audit_logs_org_created", table_name="audit_logs")
        op.drop_table("audit_logs")
