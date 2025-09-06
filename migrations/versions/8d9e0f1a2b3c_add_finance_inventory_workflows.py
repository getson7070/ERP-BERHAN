"""add finance and inventory modules with workflows"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def _table_exists(conn, name: str) -> bool:
    return name in sa.inspect(conn).get_table_names()

revision = "8d9e0f1a2b3c"
down_revision = "7c9d0e1f2g3h"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "finance_transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "org_id", sa.Integer, sa.ForeignKey("organizations.id"), nullable=False
        ),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
    )
    conn = op.get_bind()
    if not _table_exists(conn, "inventory_items"):
        op.create_table(
            "inventory_items",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column(
                "org_id", sa.Integer, sa.ForeignKey("organizations.id"), nullable=False
            ),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("quantity", sa.Integer, nullable=False),
        )
    json_type = (
        postgresql.JSONB(astext_type=sa.Text())
        if conn.dialect.name != "sqlite"
        else sa.Text()
    )
    op.create_table(
        "workflows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("module", sa.String(), nullable=False),
        sa.Column("steps", json_type, nullable=False),
        sa.Column("enabled", sa.Boolean, server_default="t", nullable=False),
        sa.Column(
            "org_id", sa.Integer, sa.ForeignKey("organizations.id"), nullable=False
        ),
    )
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("query", json_type, nullable=False),
    )
    if conn.dialect.name != "sqlite":
        for table in ("finance_transactions", "inventory_items", "workflows"):
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            op.execute(
                f"CREATE POLICY {table}_org_isolation ON {table} USING (org_id = current_setting('erp.org_id')::int)"
            )


def downgrade():
    for table in (
        "saved_searches",
        "workflows",
        "inventory_items",
        "finance_transactions",
    ):
        op.drop_table(table)
