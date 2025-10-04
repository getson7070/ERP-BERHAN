"""Fix RLS policies to use current_setting('erp.org_id')::int (idempotent & PG-only)."""

from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = "20250830_fix_rls_policies"   # keep exactly as your file uses
down_revision = "d4e5f6g7h8i"            # matches your history
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # RLS is Postgres-only; nothing to do on SQLite
        return

    # For every table in current schema that has an org_id column:
    #  - ENABLE ROW LEVEL SECURITY (safe if already enabled)
    #  - CREATE POLICY org_rls ... IF it doesn't exist yet
    op.execute(sa.text("""
    DO $plpgsql$
    DECLARE
      r record;
    BEGIN
      FOR r IN
        SELECT c.table_schema, c.table_name
        FROM information_schema.columns c
        WHERE c.table_schema = current_schema()
          AND c.column_name  = 'org_id'
      LOOP
        -- Enable RLS (idempotent: reenabling is fine)
        EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', r.table_schema, r.table_name);

        -- Create policy only if it doesn't already exist on that table
        IF NOT EXISTS (
          SELECT 1
          FROM pg_policies p
          WHERE p.schemaname = r.table_schema
            AND p.tablename  = r.table_name
            AND p.policyname = 'org_rls'
        ) THEN
          EXECUTE format(
            'CREATE POLICY org_rls ON %I.%I USING (org_id = current_setting(''erp.org_id'')::int) WITH CHECK (org_id = current_setting(''erp.org_id'')::int)',
            r.table_schema, r.table_name
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

    # Drop the org_rls policy where present; leave RLS mode itself as-is
    op.execute(sa.text("""
    DO $plpgsql$
    DECLARE
      r record;
    BEGIN
      FOR r IN
        SELECT c.table_schema, c.table_name
        FROM information_schema.columns c
        WHERE c.table_schema = current_schema()
          AND c.column_name  = 'org_id'
      LOOP
        IF EXISTS (
          SELECT 1
          FROM pg_policies p
          WHERE p.schemaname = r.table_schema
            AND p.tablename  = r.table_name
            AND p.policyname = 'org_rls'
        ) THEN
          EXECUTE format('DROP POLICY org_rls ON %I.%I', r.table_schema, r.table_name);
        END IF;
      END LOOP;
    END
    $plpgsql$;
    """))
