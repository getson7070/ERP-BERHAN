"""Fix KPI sales MV to tolerate missing order_date (PG only; sqlite no-op)."""

from alembic import op
import sqlalchemy as sa  # (kept for consistency; not strictly required)

# --- Alembic identifiers ---
revision = "20251003_fix_kpi_sales_mv"
down_revision = "5f6g7h8i9j0k"  # the revision that originally created the KPI MV
branch_labels = None
depends_on = None
# ---------------------------

def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite: skip MV work entirely
        return

    # Postgres: check columns, drop MV if present, recreate with COALESCE
    op.execute(
        """
        DO $$
        DECLARE
          has_orders      BOOLEAN;
          has_order_date  BOOLEAN;
          has_created_at  BOOLEAN;
        BEGIN
          SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'orders'
          ) INTO has_orders;

          IF has_orders THEN
            SELECT EXISTS (
              SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = 'orders' AND column_name = 'order_date'
            ) INTO has_order_date;

            SELECT EXISTS (
              SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = 'orders' AND column_name = 'created_at'
            ) INTO has_created_at;

            IF has_order_date OR has_created_at THEN
              IF to_regclass('public.kpi_sales_monthly') IS NOT NULL THEN
                EXECUTE 'DROP MATERIALIZED VIEW public.kpi_sales_monthly';
              END IF;

              EXECUTE
              'CREATE MATERIALIZED VIEW public.kpi_sales_monthly AS
                 SELECT
                   org_id,
                   DATE_TRUNC(''month'', COALESCE(order_date, created_at)) AS month,
                   SUM(total) AS total
                 FROM public.orders
                 GROUP BY org_id, DATE_TRUNC(''month'', COALESCE(order_date, created_at))';
            ELSE
              RAISE NOTICE 'orders table exists but has neither order_date nor created_at; skipping MV';
            END IF;
          ELSE
            RAISE NOTICE 'orders table not found; skipping MV';
          END IF;
        END $$;
        """
    )

def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.kpi_sales_monthly;")
