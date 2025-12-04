"""add updated_at column to roles

Revision ID: add_roles_updated_at
Revises: add_user_role_assignments
Create Date: 2025-12-03
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_roles_updated_at"
down_revision = "add_user_role_assignments"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "roles",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("roles", "updated_at")
