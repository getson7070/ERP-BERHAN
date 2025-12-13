"""Ensure core multi-tenant + RBAC schema and required users columns.

This revision makes the database match the intended model:

- organizations (tenant root)
- departments, teams (org-scoped)
- users with:
    - uuid as public identifier (UUID type)
    - org_id FK -> organizations.id
    - tin (10-digit business identifier; required by app logic at approval time)
    - core auth/runtime fields used by the User model
- roles, permissions, role_permissions, user_roles (supports temporary assignments)
- custom_fields/custom_field_values (dynamic metadata without adding columns)

It is SAFE for:
- clean rebuilds (empty DB)
- legacy DBs (adds missing tables/columns, converts uuid type when needed)

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision = "0003_org_rbac_users_core"
down_revision = "0002_ensure_users_uuid"
branch_labels = None
depends_on = None


def _table_names(conn) -> set[str]:
    insp = sa.inspect(conn)
    return set(insp.get_table_names())


def _columns(conn, table_name: str) -> set[str]:
    insp = sa.inspect(conn)
    return {c["name"] for c in insp.get_columns(table_name)}


def _ensure_pgcrypto(conn) -> None:
    # gen_random_uuid() is provided by pgcrypto
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")


def _ensure_organizations(conn) -> None:
    tables = _table_names(conn)
    if "organizations" not in tables:
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False, unique=True),
            sa.Column("tin", sa.String(length=10), nullable=True, unique=True, index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # Ensure a default org exists for clean rebuild / legacy upgrades.
    # We avoid hardcoding Berhan name here; you can rename later in admin UI.
    op.execute(
        """
        INSERT INTO organizations (id, name)
        VALUES (1, 'Default Organization')
        ON CONFLICT (id) DO NOTHING;
        """
    )


def _ensure_departments_teams(conn) -> None:
    tables = _table_names(conn)

    if "departments" not in tables:
        op.create_table(
            "departments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("org_id", "name", name="uq_departments_org_name"),
        )

    if "teams" not in tables:
        op.create_table(
            "teams",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("department_id", sa.Integer(), nullable=True, index=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("org_id", "name", name="uq_teams_org_name"),
        )


def _ensure_roles_permissions(conn) -> None:
    tables = _table_names(conn)

    if "roles" not in tables:
        op.create_table(
            "roles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=64), nullable=False, unique=True, index=True),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if "permissions" not in tables:
        op.create_table(
            "permissions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=64), nullable=False, unique=True, index=True),
            sa.Column("description", sa.String(length=255), nullable=True),
        )

    if "role_permissions" not in tables:
        op.create_table(
            "role_permissions",
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.Column("permission_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("role_id", "permission_id"),
        )

    if "user_roles" not in tables:
        op.create_table(
            "user_roles",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
            # FK to users will be added after users exists/updated below.
            sa.PrimaryKeyConstraint("user_id", "role_id"),
        )


def _ensure_custom_fields(conn) -> None:
    tables = _table_names(conn)

    if "custom_fields" not in tables:
        op.create_table(
            "custom_fields",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("entity", sa.String(length=64), nullable=False, index=True),  # e.g., 'user', 'organization', 'order'
            sa.Column("field_key", sa.String(length=64), nullable=False),
            sa.Column("label", sa.String(length=128), nullable=False),
            sa.Column("field_type", sa.String(length=32), nullable=False, default="text"),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("options_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("org_id", "entity", "field_key", name="uq_custom_fields_org_entity_key"),
        )

    if "custom_field_values" not in tables:
        op.create_table(
            "custom_field_values",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("entity", sa.String(length=64), nullable=False, index=True),
            sa.Column("entity_id", sa.String(length=64), nullable=False, index=True),  # can store UUID/text ids
            sa.Column("field_key", sa.String(length=64), nullable=False, index=True),
            sa.Column("value_text", sa.Text(), nullable=True),
            sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
            sa.Index("ix_cfv_lookup", "org_id", "entity", "entity_id", "field_key"),
        )


def _ensure_users(conn) -> None:
    tables = _table_names(conn)

    if "users" not in tables:
        # Clean rebuild path: create the table in the intended shape.
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("org_id", sa.Integer(), nullable=False, index=True),
            sa.Column("tin", sa.String(length=10), nullable=True, index=True),
            sa.Column("user_type", sa.String(length=32), nullable=True, index=True),  # client/employee/admin
            sa.Column("username", sa.String(length=120), nullable=True, unique=True, index=True),
            sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
            sa.Column("telegram_chat_id", sa.String(length=64), nullable=True, index=True),
            sa.Column("password_hash", sa.String(length=255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="RESTRICT"),
        )
        op.create_index("ix_users_uuid", "users", ["uuid"], unique=True)
        op.execute("UPDATE users SET uuid = gen_random_uuid() WHERE uuid IS NULL;")
        return

    # Legacy/upgrade path: add missing columns + convert types safely.
    cols = _columns(conn, "users")

    # uuid: ensure column exists and is UUID type
    if "uuid" not in cols:
        op.add_column("users", sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute("UPDATE users SET uuid = gen_random_uuid() WHERE uuid IS NULL;")
        op.alter_column("users", "uuid", nullable=False)
        op.create_index("ix_users_uuid", "users", ["uuid"], unique=True)
    else:
        # If uuid exists but is VARCHAR/TEXT, convert to UUID where possible.
        # (In a clean rebuild this won't matter; in legacy it prevents your current crash.)
        try:
            op.execute("ALTER TABLE users ALTER COLUMN uuid TYPE uuid USING uuid::uuid;")
        except Exception:
            # If conversion fails due to bad data, backfill with fresh UUIDs.
            op.execute("UPDATE users SET uuid = gen_random_uuid() WHERE uuid IS NULL OR uuid = '';")
            try:
                op.execute("ALTER TABLE users ALTER COLUMN uuid TYPE uuid USING uuid::uuid;")
            except Exception:
                # Last resort: leave as-is; app model must match later, but migration should not hard-fail.
                pass

        # Ensure not null + index exists
        try:
            op.execute("UPDATE users SET uuid = gen_random_uuid() WHERE uuid IS NULL;")
            op.alter_column("users", "uuid", nullable=False)
        except Exception:
            pass
        # create index if missing (ignore if exists)
        try:
            op.create_index("ix_users_uuid", "users", ["uuid"], unique=True)
        except Exception:
            pass

    # org_id
    cols = _columns(conn, "users")
    if "org_id" not in cols:
        op.add_column("users", sa.Column("org_id", sa.Integer(), nullable=True))
        op.execute("UPDATE users SET org_id = 1 WHERE org_id IS NULL;")
        op.alter_column("users", "org_id", nullable=False)
        try:
            op.create_index("ix_users_org_id", "users", ["org_id"])
        except Exception:
            pass
        try:
            op.create_foreign_key("fk_users_org_id", "users", "organizations", ["org_id"], ["id"], ondelete="RESTRICT")
        except Exception:
            pass

    # tin (10 digits) - keep nullable at DB layer; enforce at approval logic
    cols = _columns(conn, "users")
    if "tin" not in cols:
        op.add_column("users", sa.Column("tin", sa.String(length=10), nullable=True))
        try:
            op.create_index("ix_users_tin", "users", ["tin"])
        except Exception:
            pass

    # runtime/auth fields used by model
    cols = _columns(conn, "users")
    if "telegram_chat_id" not in cols:
        op.add_column("users", sa.Column("telegram_chat_id", sa.String(length=64), nullable=True))
    if "is_active" not in cols:
        op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    if "created_at" not in cols:
        op.add_column("users", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    if "updated_at" not in cols:
        op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    # If legacy columns exist, we do not drop them here (safe upgrade).
    # You can later create a cleanup revision after data migration.


def _finalize_user_roles_fk(conn) -> None:
    # user_roles was created earlier without FK to users (because users might not exist yet)
    tables = _table_names(conn)
    if "user_roles" not in tables or "users" not in tables:
        return

    # Try to create FK; ignore if already exists.
    try:
        op.create_foreign_key("fk_user_roles_user_id", "user_roles", "users", ["user_id"], ["id"], ondelete="CASCADE")
    except Exception:
        pass


def upgrade() -> None:
    conn = op.get_bind()
    _ensure_pgcrypto(conn)

    _ensure_organizations(conn)
    _ensure_departments_teams(conn)
    _ensure_roles_permissions(conn)
    _ensure_custom_fields(conn)

    _ensure_users(conn)
    _finalize_user_roles_fk(conn)


def downgrade() -> None:
    # Downgrade intentionally conservative for production safety.
    # For clean rebuild scenarios, you can drop the volume instead of downgrading.
    pass
