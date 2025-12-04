"""create user_dashboards table

Revision ID: add_user_dashboards
Revises: add_roles_updated_at
Create Date: 2025-12-03
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_user_dashboards"
down_revision = "add_roles_updated_at"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_dashboards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("layout", sa.Text, nullable=True),
        sa.Column("theme", sa.String(length=64), nullable=True),
        sa.Column("widgets", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_user_dashboards_user_id",
        "user_dashboards",
        ["user_id"],
    )


def downgrade():
    op.drop_index("ix_user_dashboards_user_id", table_name="user_dashboards")
    op.drop_table("user_dashboards")
