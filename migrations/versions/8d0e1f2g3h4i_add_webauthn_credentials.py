"""add webauthn credentials table

Revision ID: 8d0e1f2g3h4i
Revises: 7c9d0e1f2g3h
Create Date: 2025-01-01 00:00:00 UTC
"""

import sqlalchemy as sa
from alembic import op

revision = "8d0e1f2g3h4i"
down_revision = "7c9d0e1f2g3h"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "webauthn_credentials",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "org_id", sa.Integer, sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("credential_id", sa.String(512), nullable=False, unique=True),
        sa.Column("public_key", sa.LargeBinary(), nullable=False),
        sa.Column("sign_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_webauthn_credentials_user_id", "webauthn_credentials", ["user_id"]
    )
    if op.get_bind().dialect.name != "sqlite":
        op.execute("ALTER TABLE webauthn_credentials ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY webauthn_credentials_org_isolation ON webauthn_credentials USING (org_id = current_setting('erp.org_id')::int)"
        )


def downgrade():
    if op.get_bind().dialect.name != "sqlite":
        op.execute(
            "DROP POLICY IF EXISTS webauthn_credentials_org_isolation ON webauthn_credentials"
        )
    op.drop_index("ix_webauthn_credentials_user_id", table_name="webauthn_credentials")
    op.drop_table("webauthn_credentials")
