"""Add banking integration tables and extend bank_accounts."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect  # ADDED: Fixes NameError

revision = "9c2b4b3c6a5e"
down_revision = "8f5c2e7d9a4b"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "bank_accounts" not in tables:
        op.create_table(
            "bank_accounts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("bank_name", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("currency", sa.String(length=8), nullable=False, server_default="ETB"),
            sa.Column("account_number", sa.String(length=64), nullable=True),
            sa.Column("account_number_masked", sa.String(length=64), nullable=False, server_default=""),
            sa.Column("gl_account_code", sa.String(length=64), nullable=False, server_default=""),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("initial_balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_bank_accounts_org", "bank_accounts", ["org_id"])
        op.create_index("ix_bank_accounts_gl_code", "bank_accounts", ["gl_account_code"])
    else:
        existing_cols = {col["name"] for col in inspector.get_columns("bank_accounts")}
        new_columns = {
            "bank_name": sa.Column("bank_name", sa.String(length=255), nullable=False, server_default=""),
            "account_number_masked": sa.Column(
                "account_number_masked", sa.String(length=64), nullable=False, server_default=""
            ),
            "gl_account_code": sa.Column(
                "gl_account_code", sa.String(length=64), nullable=False, server_default=""
            ),
            "is_default": sa.Column(
                "is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")
            ),
            "is_active": sa.Column(
                "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
            ),
            "created_at": sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
            "created_by_id": sa.Column("created_by_id", sa.Integer(), nullable=True),
        }
        for name, column in new_columns.items():
            if name not in existing_cols:
                op.add_column("bank_accounts", column)

        idx_names = {idx["name"] for idx in inspector.get_indexes("bank_accounts")}
        if "ix_bank_accounts_gl_code" not in idx_names and "gl_account_code" in (existing_cols | set(new_columns)):
            op.create_index("ix_bank_accounts_gl_code", "bank_accounts", ["gl_account_code"])

    op.create_table(
        "bank_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False, server_default="sandbox"),
        sa.Column("api_base_url", sa.String(length=255), nullable=True),
        sa.Column("credentials_json", sa.JSON(), nullable=True),
        sa.Column("requires_two_factor", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("two_factor_method", sa.String(length=32), nullable=True),
        sa.Column("last_connected_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )

    op.create_table(
        "bank_access_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("connection_id", sa.Integer(), nullable=False, index=True),
        sa.Column("access_token", sa.String(length=4096), nullable=False),
        sa.Column("refresh_token", sa.String(length=4096), nullable=True),
        sa.Column("token_type", sa.String(length=64), nullable=True),
        sa.Column("scope", sa.String(length=512), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["connection_id"], ["bank_connections.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "bank_two_factor_challenges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("connection_id", sa.Integer(), nullable=False, index=True),
        sa.Column("challenge_type", sa.String(length=32), nullable=False),
        sa.Column("challenge_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["connection_id"], ["bank_connections.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "bank_sync_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("connection_id", sa.Integer(), nullable=True, index=True),
        sa.Column("bank_account_id", sa.Integer(), nullable=True, index=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending", index=True),
        sa.Column("requested_from", sa.Date(), nullable=True),
        sa.Column("requested_to", sa.Date(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("requested_by_id", sa.Integer(), nullable=True),
        sa.Column("statements_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lines_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["connection_id"], ["bank_connections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"], ondelete="SET NULL"),
    )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    for table in ("bank_sync_jobs", "bank_two_factor_challenges", "bank_access_tokens", "bank_connections"):
        if table in inspector.get_table_names():
            op.drop_table(table)

    existing_cols = {col["name"] for col in inspector.get_columns("bank_accounts")}
    for col in [
        "bank_name",
        "account_number_masked",
        "gl_account_code",
        "is_default",
        "is_active",
        "created_at",
        "created_by_id",
    ]:
        if col in existing_cols:
            op.drop_column("bank_accounts", col)

    idx_names = {idx["name"] for idx in inspector.get_indexes("bank_accounts")}
    if "ix_bank_accounts_gl_code" in idx_names:
        op.drop_index("ix_bank_accounts_gl_code", table_name="bank_accounts")