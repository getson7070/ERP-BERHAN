"""create KPI sales materialized view (resilient)"""

from alembic import op
import sqlalchemy as sa

revision = "5f6g7h8i9j0k"
down_revision = "4e5f6g7h8i9j"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name='orders'
                ) THEN
                    CREATE MATERIALIZED VIEW IF NOT EXISTS kpi_sales_monthly AS
                    SELECT
                        org_id,
                        DATE_TRUNC('month', order_date) AS month,
                        SUM(total) AS total
                    FROM orders
                    GROUP BY org_id, DATE_TRUNC('month', order_date);
                ELSE
                    RAISE NOTICE 'orders table not found, skipping kpi_sales_monthly creation';
                END IF;
            EXCEPTION WHEN undefined_table THEN
                RAISE NOTICE 'orders table missing, skipping MV creation';
            END $$;
            """
        )
    else:
        # SQLite fallback: regular view
        op.execute(
            """
            CREATE VIEW IF NOT EXISTS kpi_sales_monthly AS
            SELECT
                org_id,
                strftime('%Y-%m-01', order_date) AS month,
                SUM(total) AS total
            FROM orders
            GROUP BY org_id, strftime('%Y-%m-01', order_date);
            """
        )

def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP MATERIALIZED VIEW IF EXISTS kpi_sales_monthly")
    else:
        op.execute("DROP VIEW IF EXISTS kpi_sales_monthly")
