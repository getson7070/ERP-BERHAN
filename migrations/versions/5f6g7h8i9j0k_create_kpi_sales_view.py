"""create KPI sales materialized view"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '5f6g7h8i9j0k'
down_revision = '4e5f6g7h8i9j'
branch_labels = None
depends_on = None

def upgrade():
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS kpi_sales AS
        SELECT org_id, DATE_TRUNC('month', order_date) AS month, SUM(total_amount) AS total_sales
        FROM orders
        GROUP BY org_id, DATE_TRUNC('month', order_date);
        """
    )

def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS kpi_sales")
