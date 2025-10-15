"""Fix/guard RLS policy creation across finance and inventory tables (PG-only; idempotent)."""

from alembic import op
import sqlalchemy as sa

# Keep your chosen identifiers
revision = "20250830_fix_rls_policies"
down_revision = '0001_initial_core'  # tuple, not list
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(sa.text("""
    DO $plpgsql$
    DECLARE
      tbl TEXT;
    BEGIN
      FOR tbl IN SELECT unnest(ARRAY['finance_transactions','inventory_items']) LOOP

        -- Skip if table doesn't exist
        IF NOT EXISTS (
          SELECT 1 FROM information_schema.tables
          WHERE table_schema = current_schema() AND table_name = tbl
        ) THEN
          RAISE NOTICE $$table % not found; skipping RLS$$, tbl;
          CONTINUE;
        END IF;

        -- Enable RLS
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);

        -- Create policy only if not present and org_id exists
        IF EXISTS (
          SELECT 1 FROM information_schema.columns
          WHERE table_schema = current_schema() AND table_name = tbl AND column_name = 'org_id'
        ) AND NOT EXISTS (
          SELECT 1 FROM pg_policies
          WHERE schemaname = current_schema() AND tablename = tbl AND policyname = 'org_rls'
        ) THEN
          EXECUTE format(
            'CREATE POLICY org_rls ON %I USING (org_id = current_setting(''erp.org_id'')::int) WITH CHECK (org_id = current_setting(''erp.org_id'')::int)',
            tbl
          );
        END IF;

      END LOOP;
    END
    $plpgsql$;
    """))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Drop policies if present; do not disable RLS automatically
    for tbl in ("finance_transactions", "inventory_items"):
        op.execute(sa.text(f"""
        DO $plpgsql$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = current_schema() AND tablename = '{tbl}' AND policyname = 'org_rls'
          ) THEN
            EXECUTE 'DROP POLICY org_rls ON {tbl}';
          END IF;
        END
        $plpgsql$;
        """))
