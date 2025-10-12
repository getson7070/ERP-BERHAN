from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "9e0f1a2b3c4d"
down_revision = "a1b2c3d4e5b"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("data_lineage", schema="public"):
        op.create_table(
            "data_lineage",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("source_table", sa.String(255), nullable=False),
            sa.Column("target_table", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        )

def downgrade():
    op.drop_table("data_lineage")
