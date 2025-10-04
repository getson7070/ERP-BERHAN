"""Add finance and inventory modules with workflows (RLS-safe & idempotent)."""

from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = "8d9e0f1a2b3c"
down_revision = "7c9d0e1f2g3h"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dialect = bind.dialect.name

    table = "inventory_items"
    schema = None  # rely on search_path (public on PG), fine for SQLite

    # 1) Skip gracefully if table doesn't exist (works on SQLite & PG)
    try:
        has_table = insp.has_table(table, schema=schema)
    except TypeError:
        has_table = insp.has_table(table)
    if not has_table:
        return

    # 2) Ensure org_id column exists (batch_alter makes this SQLite-safe)
    cols = {c["name"] for c in insp.get_columns(table, schema=schema)}
    if "org_id" not in cols:
        with op.batch_alter_table(table, schema=schema) as batch:
            batch.add_column(sa.Column("org_id", sa.Integer(), nullable=True))

    # 3) Create index on org_id if missing (avoid duplicates)
    try:
        existing_indexes = {ix["name"] for ix in insp.get_indexes(table, schema=schema)}
    except Exception:
        existing_indexes = set()
    if "ix_inventory_items_org_id" not in existing_indexes:
        try:
            op.create_index("ix_inventory_items_org_id", table, ["org_id"], schema=schema)
        except Exception:
            # some backends or prior manual runs may already have it
            pass

    # 4) Postgres-only: enable RLS and add policy if org_id exists
    if dialect == "postgresql":
        op.execute(sa.text("""
        DO $plpgsql$
        BEGIN
          -- Enable RLS if not already
          IF NOT EXISTS (
            SELECT 1
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = current_schema()
              AND c.relname = 'inventory_items'
              AND c.relrowsecurity = true
          ) THEN
            EXECUTE 'ALTER TABLE inventory_items ENABLE ROW LEVEL SECURITY';
          END IF;

          -- Create policy only if org_id column exists
          IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name   = 'inventory_items'
              AND column_name  = 'org_id'
          ) THEN
            IF NOT EXISTS (
              SELECT 1
              FROM pg_policies
              WHERE schemaname = current_schema()
                AND tablename  = 'inventory_items'
                AND policyname = 'inventory_items_org_isolation'
            ) THEN
              EXECUTE 'CREATE POLICY inventory_items_org_isolation
                       ON inventory_items
                       USING (org_id = current_setting(''erp.org_id'')::int)';
            END IF;
          ELSE
            RAISE NOTICE $$inventory_items.org_id missing; skipping RLS policy$$;
          END IF;
        END
        $plpgsql$;
        """))


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    table = "inventory_items"
    schema = None

    # PG: drop the policy if present (safe/no-op otherwise)
    if dialect == "postgresql":
        op.execute(sa.text("""
        DO $plpgsql$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM pg_policies
            WHERE schemaname = current_schema()
              AND tablename  = 'inventory_items'
              AND policyname = 'inventory_items_org_isolation'
          ) THEN
            EXECUTE 'DROP POLICY inventory_items_org_isolation ON inventory_items';
          END IF;
        END
        $plpgsql$;
        """))

    # Drop index if present (column removal is intentionally skipped to avoid data loss)
    try:
        op.drop_index("ix_inventory_items_org_id", table_name=table, schema=schema)
    except Exception:
        pass
