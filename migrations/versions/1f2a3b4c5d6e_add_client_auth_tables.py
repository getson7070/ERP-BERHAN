"""Add client auth tables.

PROBLEM THIS FIXES
------------------
On a fresh database, this revision failed because it creates
`client_role_assignments` with an FK to `roles(id)`, but the `roles`
table was never created in the current clean-chain install.

This revision is now self-bootstrapping and idempotent:
- Ensures `roles` exists (creates it if missing).
- Creates client auth tables only if they don't exist.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "1f2a3b4c5d6e"
down_revision = "f4a5c6d7e8f9"
branch_labels = None
depends_on = None


def _has_table(insp, name: str) -> bool:
    return insp.has_table(name)


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # ---------------------------------------------------------------
    # 0) Ensure RBAC base table exists (roles)
    # ---------------------------------------------------------------
    if not _has_table(insp, "roles"):
        op.create_table(
            "roles",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(length=64), nullable=False, unique=True),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=False),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    # ---------------------------------------------------------------
    # 1) Client accounts
    # ---------------------------------------------------------------
    if not _has_table(insp, "client_accounts"):
        op.create_table(
            "client_accounts",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=True, unique=True),
            sa.Column("phone", sa.String(length=32), nullable=True),
            sa.Column("password_hash", sa.String(length=255), nullable=True),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=False),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_client_accounts_org_id", "client_accounts", ["org_id"])
        op.create_index("ix_client_accounts_email", "client_accounts", ["email"], unique=True)

    # ---------------------------------------------------------------
    # 2) Client API keys (optional but useful for portal / integrations)
    # ---------------------------------------------------------------
    if not _has_table(insp, "client_api_keys"):
        op.create_table(
            "client_api_keys",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("client_account_id", sa.Integer(), nullable=False),
            sa.Column("label", sa.String(length=128), nullable=True),
            sa.Column("key_hash", sa.String(length=255), nullable=False, unique=True),
            sa.Column("last_used_at", sa.DateTime(timezone=False), nullable=True),
            sa.Column(
                "revoked",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=False),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(
                ["client_account_id"],
                ["client_accounts.id"],
                ondelete="CASCADE",
                name="fk_client_api_keys_client_account_id_client_accounts",
            ),
        )
        op.create_index(
            "ix_client_api_keys_client_account_id",
            "client_api_keys",
            ["client_account_id"],
        )

    # ---------------------------------------------------------------
    # 3) Client sessions / refresh tokens
    # ---------------------------------------------------------------
    if not _has_table(insp, "client_sessions"):
        op.create_table(
            "client_sessions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("client_account_id", sa.Integer(), nullable=False),
            sa.Column("refresh_token_hash", sa.String(length=255), nullable=False, unique=True),
            sa.Column("expires_at", sa.DateTime(timezone=False), nullable=False),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=False),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(
                ["client_account_id"],
                ["client_accounts.id"],
                ondelete="CASCADE",
                name="fk_client_sessions_client_account_id_client_accounts",
            ),
        )
        op.create_index(
            "ix_client_sessions_client_account_id",
            "client_sessions",
            ["client_account_id"],
        )

    # ---------------------------------------------------------------
    # 4) Client ↔ Role assignments (this is what failed before)
    # ---------------------------------------------------------------
    if not _has_table(insp, "client_role_assignments"):
        op.create_table(
            "client_role_assignments",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("client_account_id", sa.Integer(), nullable=False),
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=False),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(
                ["client_account_id"],
                ["client_accounts.id"],
                ondelete="CASCADE",
                name="fk_client_role_assignments_client_account_id_client_accounts",
            ),
            sa.ForeignKeyConstraint(
                ["role_id"],
                ["roles.id"],
                ondelete="CASCADE",
                name="fk_client_role_assignments_role_id_roles",
            ),
            sa.UniqueConstraint(
                "client_account_id",
                "role_id",
                name="uq_client_role",
            ),
        )
        op.create_index(
            "ix_client_role_assignments_client_account_id",
            "client_role_assignments",
            ["client_account_id"],
        )
        op.create_index(
            "ix_client_role_assignments_role_id",
            "client_role_assignments",
            ["role_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # Drop child tables first
    if _has_table(insp, "client_role_assignments"):
        op.drop_index("ix_client_role_assignments_role_id", table_name="client_role_assignments")
        op.drop_index("ix_client_role_assignments_client_account_id", table_name="client_role_assignments")
        op.drop_table("client_role_assignments")

    if _has_table(insp, "client_sessions"):
        op.drop_index("ix_client_sessions_client_account_id", table_name="client_sessions")
        op.drop_table("client_sessions")

    if _has_table(insp, "client_api_keys"):
        op.drop_index("ix_client_api_keys_client_account_id", table_name="client_api_keys")
        op.drop_table("client_api_keys")

    if _has_table(insp, "client_accounts"):
        op.drop_index("ix_client_accounts_email", table_name="client_accounts")
        op.drop_index("ix_client_accounts_org_id", table_name="client_accounts")
        op.drop_table("client_accounts")

    # We do NOT drop roles on downgrade here because roles are a core RBAC table
    # likely used by many other modules. If you truly want to remove, do it in a
    # dedicated RBAC downgrade revision.
