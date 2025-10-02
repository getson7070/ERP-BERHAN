"""add core module tables (minimal)"""

from alembic import op
import sqlalchemy as sa

revision = "7c9d0e1f2g3h"
down_revision = "c3d4e5f6g7h"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # organizations
    if dialect == "postgresql":
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS organizations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            """
        )
    else:
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(255), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        )

    # orders (only the columns needed by KPI view)
    if dialect == "postgresql":
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                order_date TIMESTAMP NOT NULL,
                total INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS ix_orders_org_id ON orders(org_id);
            CREATE INDEX IF NOT EXISTS ix_orders_order_date ON orders(order_date);
            """
        )
    else:
        op.create_table(
            "orders",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("org_id", sa.Integer, nullable=False),
            sa.Column("order_date", sa.DateTime, nullable=False),
            sa.Column("total", sa.Integer, nullable=False),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_orders_org_id", "orders", ["org_id"])
        op.create_index("ix_orders_order_date", "orders", ["order_date"])

def downgrade() -> None:
    op.drop_table("orders")
    op.drop_table("organizations")
