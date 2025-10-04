from alembic import op
import sqlalchemy as sa

# ... keep your Alembic identifiers above ...

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dialect = bind.dialect.name

    table = "inventory_items"
    schema = None  # rely on search_path in PG, fine for SQLite

    # If the table isn't there, skip everything gracefully
    try:
        has_table = insp.has_table(table, schema=schema)
    except TypeError:
        has_table = insp.has_table(table)
    if not has_table:
        return

    # Add org_id if missing
    cols = {c["name"] for c in insp.get_columns(table, schema=schema)}
    if "org_id" not in cols:
        with op.batch_alter_table(table, schema=schema) as batch:
            batch.add_column(sa.Column("org_id", sa.Integer(), nullable=True))
        # optional index on org_id (skip on SQLite silently)
        try:
            op.create_index("ix_inventory_items_org_id", table, ["org_id"], schema=schema)
        except Exception:
            pass

    # Only Postgres supports RLS/policies
    if dialect == "postgresql":
        # Enable RLS on the table (idempotent)
        op.execute(sa.text("ALTER TABLE inventory_items ENABLE ROW LEVEL SECURITY"))

        # Create policy if missing (use proper dollar-quoting)
        op.execute(sa.text("""
        DO $plpgsql$
        BEGIN
          IF NOT EXISTS (
            SELECT 1
            FROM pg_policies
            WHERE schemaname = current_schema()
              AND tablename  = 'inventory_items'
              AND policyname = 'inventory_items_org_isolation'
          ) THEN
            CREATE POLICY inventory_items_org_isolation
              ON inventory_items
              USING (org_id = current_setting('erp.org_id')::int);
          END IF;
        END
        $plpgsql$;
        """))
