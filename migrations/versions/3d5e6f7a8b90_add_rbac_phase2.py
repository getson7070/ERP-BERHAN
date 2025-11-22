"""Add Phase-2 RBAC policy and role request tables."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3d5e6f7a8b90"
down_revision = "2c3d4e5f6780"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rbac_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(length=128), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.UniqueConstraint("org_id", "name", name="uq_policy_name"),
    )

    op.create_table(
        "rbac_policy_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("policy_id", sa.Integer(), sa.ForeignKey("rbac_policies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role_key", sa.String(length=64), nullable=False, index=True),
        sa.Column("resource", sa.String(length=128), nullable=False, index=True),
        sa.Column("action", sa.String(length=64), nullable=False, index=True),
        sa.Column("effect", sa.String(length=8), nullable=False, server_default="allow"),
        sa.Column("condition_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_table(
        "role_hierarchy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("parent_role", sa.String(length=64), nullable=False, index=True),
        sa.Column("child_role", sa.String(length=64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("org_id", "parent_role", "child_role", name="uq_role_hierarchy"),
    )

    op.create_table(
        "role_assignment_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("requester_id", sa.Integer(), nullable=False, index=True),
        sa.Column("target_user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("role_key", sa.String(length=64), nullable=False, index=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending", index=True),
        sa.Column("reviewed_by_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index(
        "ix_policy_role_res_act",
        "rbac_policy_rules",
        ["org_id", "role_key", "resource", "action"],
    )
    op.create_index(
        "ix_role_req_org_status",
        "role_assignment_requests",
        ["org_id", "status"],
    )


def downgrade():
    op.drop_index("ix_role_req_org_status", table_name="role_assignment_requests")
    op.drop_index("ix_policy_role_res_act", table_name="rbac_policy_rules")
    op.drop_table("role_assignment_requests")
    op.drop_table("role_hierarchy")
    op.drop_table("rbac_policy_rules")
    op.drop_table("rbac_policies")
