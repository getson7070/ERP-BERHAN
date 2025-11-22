"""Add MFA, backup codes, user sessions, and active flag."""

from alembic import op
import sqlalchemy as sa


revision = "a12b34c56d78"
down_revision = "f4a5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"], unique=False)

    op.create_table(
        "user_mfa",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("totp_secret", sa.String(length=64), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("org_id", "user_id", name="uq_user_mfa"),
    )
    op.create_index(op.f("ix_user_mfa_org_id"), "user_mfa", ["org_id"], unique=False)
    op.create_index(op.f("ix_user_mfa_user_id"), "user_mfa", ["user_id"], unique=False)

    op.create_table(
        "user_mfa_backup_codes",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_user_mfa_backup_codes_org_id"), "user_mfa_backup_codes", ["org_id"], unique=False)
    op.create_index(op.f("ix_user_mfa_backup_codes_user_id"), "user_mfa_backup_codes", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_mfa_backup_codes_code_hash"), "user_mfa_backup_codes", ["code_hash"], unique=False)

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_id", sa.Integer(), nullable=True),
        sa.UniqueConstraint("org_id", "session_id", name="uq_session_id"),
    )
    op.create_index(op.f("ix_user_sessions_org_id"), "user_sessions", ["org_id"], unique=False)
    op.create_index(op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_sessions_session_id"), "user_sessions", ["session_id"], unique=False)


def downgrade():
    op.drop_table("user_sessions")
    op.drop_table("user_mfa_backup_codes")
    op.drop_table("user_mfa")
    op.drop_index(op.f("ix_users_is_active"), table_name="users")
    op.drop_column("users", "is_active")
