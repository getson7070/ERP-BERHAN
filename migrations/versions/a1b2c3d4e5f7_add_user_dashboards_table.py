from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "a1b2c3d4e5f7"
down_revision = "9e0f1a2b3c4d"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # table creation
    if not insp.has_table("user_dashboards", schema="public"):
        op.create_table(
            "user_dashboards",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, nullable=False),
            sa.Column("layout", sa.Text, nullable=False),
            sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
        )

    # unique(user_id)
    if not bind.execute(text(
        "SELECT 1 FROM pg_constraint WHERE conname = 'user_dashboards_user_id_key'"
    )).scalar():
        op.create_unique_constraint(
            "user_dashboards_user_id_key",
            "user_dashboards",
            ["user_id"],
        )

    # FK(user_id) -> users(id)
    if not bind.execute(text(
        "SELECT 1 FROM pg_constraint WHERE conname = 'user_dashboards_user_id_fkey'"
    )).scalar():
        op.create_foreign_key(
            "user_dashboards_user_id_fkey",
            "user_dashboards",
            "users",
            ["user_id"],
            ["id"],
        )

def downgrade():
    op.drop_constraint("user_dashboards_user_id_fkey", "user_dashboards", type_="foreignkey")
    op.drop_constraint("user_dashboards_user_id_key", "user_dashboards", type_="unique")
    op.drop_table("user_dashboards")
