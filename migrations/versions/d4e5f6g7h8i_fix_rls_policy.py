"""Fix RLS policy to use erp.org_id (PG-only, idempotent, existence-aware)."""

from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = "d4e5f6g7h8i"
down_revision = "8d9e0f1a2b3c"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # RLS is PG-only; no-op on SQLite/others
        return

    # Guard everything: table existence, column existence, RLS enabled, policy present
    op.execute(sa.text("""
    DO $plpgsql$
    DECLARE
      sch   text := current_schema();
      rel   text;
      fq    text;
      has_org boolean;
    BEGIN
      -- Add any other org-scoped tables here if needed
      FOREACH rel IN ARRAY ARRAY['inventory_items','finance_transactions']
      LOOP
        fq := quote_ident(sch) || '.' || quote_ident(rel);

        -- Table present?
        IF to_regclass(fq) IS NULL THEN
          RAISE NOTICE $$% not found; skipping RLS$$, fq;
          CONTINUE;
        END IF;

        -- org_id column present?
        SELECT EXISTS (
          SELECT 1
          FROM information_schema.columns
          WHERE table_schema = sch
            AND table_name   = rel
            AND column_name  = 'org_id'
        ) INTO has_org;

        IF NOT has_org THEN
          RAISE NOTICE $$%.org_id missing; skipping policy$$, fq;
          CONTINUE;
        END IF;

        -- Enable RLS if not already
        IF NOT EXISTS (
          SELECT 1
          FROM pg_class c
          JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE n.nspname = sch
            AND c.relname = rel
            AND c.relrowsecurity = true
        ) THEN
          EXECUTE 'ALTER TABLE ' || fq || ' ENABLE ROW LEVEL SECURITY';
        END IF;

        -- Create policy if it doesn't exist yet
        IF NOT EXISTS (
          SELECT 1
          FROM pg_policies
          WHERE schemaname = sch
            AND tablename  = rel
            AND policyname = 'org_rls'
        ) THEN
          EXECUTE 'CREATE POLICY org_rls ON ' || fq ||
                  ' USING (org_id = current_setting(''erp.org_id'')::int) ' ||
                  ' WITH CHECK (org_id = current_setting(''erp.org_id'')::int)';
        END IF;
      END LOOP;
    END
    $plpgsql$;
    """))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(sa.text("""
    DO $plpgsql$
    DECLARE
      sch text := current_schema();
      rel text;
      fq  text;
    BEGIN
      FOREACH rel IN ARRAY ARRAY['inventory_items','finance_transactions']
      LOOP
        fq := quote_ident(sch) || '.' || quote_ident(rel);

        IF to_regclass(fq) IS NULL THEN
          CONTINUE;
        END IF;

        IF EXISTS (
          SELECT 1
          FROM pg_policies
          WHERE schemaname = sch
            AND tablename  = rel
            AND policyname = 'org_rls'
        ) THEN
          EXECUTE 'DROP POLICY org_rls ON ' || fq;
        END IF;
      END LOOP;
    END
    $plpgsql$;
    """))
