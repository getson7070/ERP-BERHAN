"""add user_dashboards table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7_add_user_dashboards_table"
down_revision = "9e0f1a2b3c4d_add_data_lineage_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_dashboards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("layout", sa.Text(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade():
    op.drop_table("user_dashboards")
