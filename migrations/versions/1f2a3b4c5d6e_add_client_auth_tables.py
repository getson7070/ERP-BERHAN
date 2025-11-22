"""add client auth tables"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "1f2a3b4c5d6e"
down_revision = "f4a5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "client_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("org_id", "email", name="uq_client_email"),
        sa.UniqueConstraint("org_id", "phone", name="uq_client_phone"),
    )
    op.create_index("ix_client_accounts_org", "client_accounts", ["org_id"])
    op.create_index("ix_client_accounts_client", "client_accounts", ["client_id"])
    op.create_index("ix_client_accounts_email", "client_accounts", ["email"])
    op.create_index("ix_client_accounts_phone", "client_accounts", ["phone"])

    op.create_table(
        "client_role_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_account_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("client_account_id", "role_id", name="uq_client_role"),
    )
    op.create_index("ix_client_role_assignments_account", "client_role_assignments", ["client_account_id"])
    op.create_index("ix_client_role_assignments_role", "client_role_assignments", ["role_id"])

    op.create_table(
        "client_verifications",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("client_account_id", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_client_verifications_org", "client_verifications", ["org_id"])
    op.create_index("ix_client_verifications_account", "client_verifications", ["client_account_id"])
    op.create_index("ix_client_verifications_expires", "client_verifications", ["expires_at"])

    op.create_table(
        "client_password_resets",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("client_account_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_client_resets_org", "client_password_resets", ["org_id"])
    op.create_index("ix_client_resets_account", "client_password_resets", ["client_account_id"])
    op.create_index("ix_client_resets_token", "client_password_resets", ["token_hash"])
    op.create_index("ix_client_resets_expires", "client_password_resets", ["expires_at"])

    op.create_table(
        "client_oauth_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("client_account_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("provider_email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("org_id", "provider", "provider_user_id", name="uq_client_oauth"),
    )
    op.create_index("ix_client_oauth_org", "client_oauth_accounts", ["org_id"])
    op.create_index("ix_client_oauth_account", "client_oauth_accounts", ["client_account_id"])
    op.create_index("ix_client_oauth_provider", "client_oauth_accounts", ["provider"])
    op.create_index("ix_client_oauth_provider_user", "client_oauth_accounts", ["provider_user_id"])


def downgrade():
    op.drop_table("client_oauth_accounts")
    op.drop_table("client_password_resets")
    op.drop_table("client_verifications")
    op.drop_table("client_role_assignments")
    op.drop_table("client_accounts")
