"""Fix KPI sales MV to tolerate missing order_date"""

from alembic import op
import sqlalchemy as sa

# pick any unique id; keep it lowercase/hex-ish
revision = "20251003_fix_kpi_sales_mv"
down_revision = "5f6g7h8i9j0k"   # ← the revision that created the KPI MV
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # SQLite: no-op
    if dialect == "sqlite":
        return

    # Postgres: drop and recreate MV with COALESCE(order_date, created_at)
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.kpi_sales_monthly') IS NOT NULL THEN
                DROP MATERIALIZED VIEW kpi_sales_monthly;
            END IF;

            -- Build over orders(org_id, total, order_date?) but fall back to created_at if order_date doesn't exist
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'orders' AND column_name = 'order_date'
            ) THEN
                CREATE MATERIALIZED VIEW kpi_sales_monthly AS
                SELECT
                    org_id,
                    DATE_TRUNC('month', order_date) AS month,
                    SUM(total) AS total
                FROM orders
                GROUP BY org_id, DATE_TRUNC('month', order_date);
            ELSIF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'orders' AND column_name = 'created_at'
            ) THEN
                CREATE MATERIALIZED VIEW kpi_sales_monthly AS
                SELECT
                    org_id,
                    DATE_TRUNC('month', created_at) AS month,
                    SUM(total) AS total
                FROM orders
                GROUP BY org_id, DATE_TRUNC('month', created_at);
            ELSE
                RAISE NOTICE 'orders table/columns missing, skipping MV creation';
            END IF;
        END $$;
        """
    )

def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    op.execute("DROP MATERIALIZED VIEW IF EXISTS kpi_sales_monthly;")
