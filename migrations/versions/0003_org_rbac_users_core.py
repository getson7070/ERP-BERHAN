"""Ensure core multi-tenant + RBAC schema and required users columns.

SAFE FOR:
- clean rebuilds
- legacy DBs
- repeated alembic upgrades

This migration NEVER inserts invalid rows.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_org_rbac_users_core"
down_revision = "0002_ensure_users_uuid"
branch_labels = None
depends_on = None


def _table_names(conn) -> set[str]:
    return set(sa.inspect(conn).get_table_names())


def _columns(conn, table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(conn).get_columns(table)}


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # Ensure pgcrypto
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # ------------------------------------------------------------------
    # Organizations (ROOT TENANT)
    # ------------------------------------------------------------------
    tables = _table_names(conn)

    if "organizations" not in tables:
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tin", sa.String(length=10), nullable=False, unique=True, index=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("email", sa.String(length=255)),
            sa.Column("phone", sa.String(length=64)),
            sa.Column("address_text", sa.Text()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # ALWAYS ensure default org exists with VALID tin
    op.execute(
        """
        INSERT INTO organizations (id, tin, name, is_active)
        VALUES (1, '0000000000', 'Default Organization', TRUE)
        ON CONFLICT (id) DO UPDATE
          SET tin = COALESCE(organizations.tin, EXCLUDED.tin),
              name = COALESCE(organizations.name, EXCLUDED.name);
        """
    )

    # ------------------------------------------------------------------
    # USERS
    # ------------------------------------------------------------------
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=False),
            sa.Column("tin", sa.String(length=10)),
            sa.Column("user_type", sa.String(length=32)),
            sa.Column("username", sa.String(length=120), unique=True),
            sa.Column("email", sa.String(length=255), nullable=False, unique=True),
            sa.Column("telegram_chat_id", sa.String(length=64)),
            sa.Column("password_hash", sa.String(length=255)),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="RESTRICT"),
        )
        op.create_index("ix_users_uuid", "users", ["uuid"], unique=True)

    else:
        cols = _columns(conn, "users")
        if "uuid" not in cols:
            op.add_column("users", sa.Column("uuid", postgresql.UUID(as_uuid=True)))
            op.execute("UPDATE users SET uuid = gen_random_uuid() WHERE uuid IS NULL")
            op.alter_column("users", "uuid", nullable=False)
            op.create_index("ix_users_uuid", "users", ["uuid"], unique=True)

        if "org_id" not in cols:
            op.add_column("users", sa.Column("org_id", sa.Integer()))
            op.execute("UPDATE users SET org_id = 1 WHERE org_id IS NULL")
            op.alter_column("users", "org_id", nullable=False)
            op.create_foreign_key("fk_users_org", "users", "organizations", ["org_id"], ["id"])

    # ------------------------------------------------------------------
    # ROLES / PERMISSIONS / USER_ROLES
    # ------------------------------------------------------------------
    if "roles" not in tables:
        op.create_table(
            "roles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("name", sa.String(length=64), nullable=False),
            sa.Column("description", sa.String(length=255)),
            sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("org_id", "name", name="uq_roles_org_name"),
        )

    if "permissions" not in tables:
        op.create_table(
            "permissions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(length=64), nullable=False, unique=True),
            sa.Column("module", sa.String(length=64), nullable=False),
            sa.Column("description", sa.String(length=255)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if "user_roles" not in tables:
        op.create_table(
            "user_roles",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True)),
            sa.PrimaryKeyConstraint("user_id", "role_id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        )


def downgrade() -> None:
    pass
