"""Fix KPI sales MV to tolerate missing order_date (PG only; sqlite no-op)."""

from alembic import op
import sqlalchemy as sa  # keep import for Alembic compatibility

# Alembic IDs
revision = "20251003_fix_kpi_sales_mv"
down_revision = "5f6g7h8i9j0k"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # No materialized views on SQLite -> no-op
        return

    # Postgres: check for table/columns and (re)create MV safely
    op.execute(
        """
        DO $$
        DECLARE
          has_orders      BOOLEAN;
          has_order_date  BOOLEAN;
          has_created_at  BOOLEAN;
          ts_col          TEXT;
        BEGIN
          SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'orders'
          ) INTO has_orders;

          IF NOT has_orders THEN
            RAISE NOTICE 'orders table not found; skipping MV';
            RETURN;
          END IF;

          SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'orders' AND column_name = 'order_date'
          ) INTO has_order_date;

          SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'orders' AND column_name = 'created_at'
          ) INTO has_created_at;

          IF NOT (has_order_date OR has_created_at) THEN
            RAISE NOTICE 'orders table exists but has neither order_date nor created_at; skipping MV';
            RETURN;
          END IF;

          ts_col := CASE
                      WHEN has_order_date THEN 'order_date'
                      ELSE 'created_at'
                    END;

          -- Drop if present to avoid dependency issues; then create (no IF NOT EXISTS needed)
          IF to_regclass('public.kpi_sales_monthly') IS NOT NULL THEN
            EXECUTE 'DROP MATERIALIZED VIEW public.kpi_sales_monthly';
          END IF;

          -- Use dollar-quoting + format() with %I to safely inject identifier
          EXECUTE format($fmt$
            CREATE MATERIALIZED VIEW public.kpi_sales_monthly AS
            SELECT
              org_id,
              DATE_TRUNC('month', %1$I) AS month,
              SUM(total) AS total
            FROM public.orders
            GROUP BY org_id, DATE_TRUNC('month', %1$I)
          $fmt$, ts_col);

        END $$;
        """
    )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.kpi_sales_monthly;")
