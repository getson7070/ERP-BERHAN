"""create user_role_assignments table

Revision ID: add_user_role_assignments
Revises: f7a87f922530
Create Date: 2025-12-03

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_user_role_assignments"
down_revision = "f7a87f922530"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_role_assignments",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade():
    op.drop_table("user_role_assignments")
