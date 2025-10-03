"""create KPI sales materialized view (column-aware / PG-only)"""

from alembic import op
import sqlalchemy as sa

# Keep these IDs the same as your repo shows for this migration
revision = "5f6g7h8i9j0k"
down_revision = "4e5f6g7h8i9j"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        # Create MV only if table exists AND at least one of the date columns exists.
        # Use COALESCE(order_date, created_at) so we don't hard-require order_date.
        op.execute(sa.text("""
        DO $$
        DECLARE
          has_orders      BOOLEAN;
          has_order_date  BOOLEAN;
          has_created_at  BOOLEAN;
        BEGIN
          SELECT EXISTS(
            SELECT 1 FROM information_schema.tables
            WHERE table_schema='public' AND table_name='orders'
          ) INTO has_orders;

          IF has_orders THEN
            SELECT EXISTS(
              SELECT 1 FROM information_schema.columns
              WHERE table_schema='public' AND table_name='orders' AND column_name='order_date'
            ) INTO has_order_date;

            SELECT EXISTS(
              SELECT 1 FROM information_schema.columns
              WHERE table_schema='public' AND table_name='orders' AND column_name='created_at'
            ) INTO has_created_at;

            IF has_order_date OR has_created_at THEN
              EXECUTE
              'CREATE MATERIALIZED VIEW IF NOT EXISTS kpi_sales_monthly AS
                 SELECT
                   org_id,
                   DATE_TRUNC(''month'', COALESCE(order_date, created_at)) AS month,
                   SUM(total) AS total
                 FROM orders
                 GROUP BY org_id, DATE_TRUNC(''month'', COALESCE(order_date, created_at))';
            ELSE
              RAISE NOTICE ''orders table exists but has neither order_date nor created_at; skipping MV'';
            END IF;
          ELSE
            RAISE NOTICE ''orders table not found; skipping MV'';
          END IF;
        END $$;
        """))
    # no-op for SQLite and other dialects


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS kpi_sales_monthly;"))
