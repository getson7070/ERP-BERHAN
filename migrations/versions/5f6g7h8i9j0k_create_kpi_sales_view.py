"""Create KPI sales materialized view (PG only; sqlite no-op)."""

from alembic import op
import sqlalchemy as sa

revision = "5f6g7h8i9j0k"
down_revision = "4e5f6g7h8i9j"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite has no MVs
        return

    op.execute(sa.text("""
    DO $plpgsql$
    DECLARE
      has_orders      BOOLEAN;
      has_order_date  BOOLEAN;
      has_created_at  BOOLEAN;
    BEGIN
      SELECT EXISTS(
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = current_schema() AND table_name = 'orders'
      ) INTO has_orders;

      IF NOT has_orders THEN
        RAISE NOTICE $$orders table not found; skipping MV creation$$;
        RETURN;
      END IF;

      SELECT EXISTS(
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'orders' AND column_name = 'order_date'
      ) INTO has_order_date;

      SELECT EXISTS(
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'orders' AND column_name = 'created_at'
      ) INTO has_created_at;

      IF NOT (has_order_date OR has_created_at) THEN
        RAISE NOTICE $$orders table exists but has neither order_date nor created_at; skipping MV creation$$;
        RETURN;
      END IF;

      IF EXISTS (
        SELECT 1 FROM pg_matviews
        WHERE schemaname = current_schema() AND matviewname = 'kpi_sales_monthly'
      ) THEN
        RAISE NOTICE $$kpi_sales_monthly already exists; leaving as-is$$;
        RETURN;
      END IF;

      EXECUTE $sql$
        CREATE MATERIALIZED VIEW kpi_sales_monthly AS
        SELECT
          org_id,
          DATE_TRUNC('month', COALESCE(order_date, created_at)) AS month,
          SUM(total) AS total
        FROM orders
        GROUP BY org_id, DATE_TRUNC('month', COALESCE(order_date, created_at));
      $sql$;
    END
    $plpgsql$;
    """))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS kpi_sales_monthly"))
