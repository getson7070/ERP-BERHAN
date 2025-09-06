"""add data lineage table"""

from alembic import op
import sqlalchemy as sa

revision = "9e0f1a2b3c4d"
down_revision = "a1b2c3d4e5b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "data_lineage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_table", sa.String(length=255), nullable=False),
        sa.Column("target_table", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade():
    op.drop_table("data_lineage")
