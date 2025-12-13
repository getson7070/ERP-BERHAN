"""Base core schema for organizations + RBAC + custom fields.

Revision ID: 739649794424
Revises: None
Create Date: 2025-12-12
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "739649794424"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Organizations (Institutions / Companies) ---
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tin", sa.String(length=10), nullable=False),  # 10-digit, may start with 0
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address_text", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("tin", name="uq_organizations_tin"),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"], unique=False)

    # --- Departments (per org) ---
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("org_id", "name", name="uq_departments_org_name"),
    )
    op.create_index("ix_departments_org_id", "departments", ["org_id"], unique=False)

    # --- Teams (per org, optional department) ---
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("org_id", "name", name="uq_teams_org_name"),
    )
    op.create_index("ix_teams_org_id", "teams", ["org_id"], unique=False)
    op.create_index("ix_teams_department_id", "teams", ["department_id"], unique=False)

    # --- Roles (global or per org) ---
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("org_id", "name", name="uq_roles_org_name"),
    )
    op.create_index("ix_roles_org_id", "roles", ["org_id"], unique=False)

    # --- Permissions (global catalog) ---
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_index("ix_permissions_module", "permissions", ["module"], unique=False)

    # --- Role -> Permission mapping ---
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_perm"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"], unique=False)
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"], unique=False)

    # --- Users (Employees / Clients / Admin) ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False),

        sa.Column("user_type", sa.String(length=32), nullable=False, server_default=sa.text("'employee'")),
        sa.Column("tin", sa.String(length=10), nullable=True),  # employee/client TIN requirement enforced at app layer
        sa.Column("full_name", sa.String(length=255), nullable=True),

        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),

        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("position", sa.String(length=255), nullable=True),

        sa.Column("telegram_chat_id", sa.String(length=64), nullable=True),

        sa.Column("password_hash", sa.String(length=255), nullable=True),

        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),

        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_org_id", "users", ["org_id"], unique=False)
    op.create_index("ix_users_user_type", "users", ["user_type"], unique=False)
    op.create_index("ix_users_tin", "users", ["tin"], unique=False)

    # --- User -> Role mapping ---
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"], unique=False)
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"], unique=False)

    # --- Per-user permission overrides (allow/deny) ---
    op.create_table(
        "user_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.UniqueConstraint("user_id", "permission_id", name="uq_user_permissions_user_perm"),
    )
    op.create_index("ix_user_permissions_user_id", "user_permissions", ["user_id"], unique=False)
    op.create_index("ix_user_permissions_permission_id", "user_permissions", ["permission_id"], unique=False)

    # --- Custom Fields (dynamic schema extension) ---
    op.create_table(
        "custom_fields",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),  # e.g. "users", "orders", "tenders"
        sa.Column("field_key", sa.String(length=128), nullable=False),
        sa.Column("field_type", sa.String(length=32), nullable=False, server_default=sa.text("'text'")),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.UniqueConstraint("org_id", "entity_type", "field_key", name="uq_custom_fields_org_entity_key"),
    )
    op.create_index("ix_custom_fields_org_id", "custom_fields", ["org_id"], unique=False)
    op.create_index("ix_custom_fields_entity_type", "custom_fields", ["entity_type"], unique=False)

    op.create_table(
        "custom_field_values",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_uuid", sa.String(length=36), nullable=False),  # public id reference (users.uuid, orders.uuid, etc.)
        sa.Column("field_id", sa.Integer(), sa.ForeignKey("custom_fields.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.UniqueConstraint("org_id", "entity_type", "entity_uuid", "field_id", name="uq_custom_field_values_key"),
    )
    op.create_index("ix_custom_field_values_org_id", "custom_field_values", ["org_id"], unique=False)
    op.create_index("ix_custom_field_values_entity", "custom_field_values", ["entity_type", "entity_uuid"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_custom_field_values_entity", table_name="custom_field_values")
    op.drop_index("ix_custom_field_values_org_id", table_name="custom_field_values")
    op.drop_table("custom_field_values")

    op.drop_index("ix_custom_fields_entity_type", table_name="custom_fields")
    op.drop_index("ix_custom_fields_org_id", table_name="custom_fields")
    op.drop_table("custom_fields")

    op.drop_index("ix_user_permissions_permission_id", table_name="user_permissions")
    op.drop_index("ix_user_permissions_user_id", table_name="user_permissions")
    op.drop_table("user_permissions")

    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_table("user_roles")

    op.drop_index("ix_users_tin", table_name="users")
    op.drop_index("ix_users_user_type", table_name="users")
    op.drop_index("ix_users_org_id", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_role_permissions_permission_id", table_name="role_permissions")
    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_table("role_permissions")

    op.drop_index("ix_permissions_module", table_name="permissions")
    op.drop_table("permissions")

    op.drop_index("ix_roles_org_id", table_name="roles")
    op.drop_table("roles")

    op.drop_index("ix_teams_department_id", table_name="teams")
    op.drop_index("ix_teams_org_id", table_name="teams")
    op.drop_table("teams")

    op.drop_index("ix_departments_org_id", table_name="departments")
    op.drop_table("departments")

    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_table("organizations")
