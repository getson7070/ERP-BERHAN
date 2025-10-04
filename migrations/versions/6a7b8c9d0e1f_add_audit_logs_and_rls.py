"""Add audit_logs table and guarded RLS policies (PG-safe, idempotent)."""

from alembic import op
import sqlalchemy as sa

revision = "6a7b8c9d0e1f"
down_revision = "5f6g7h8i9j0k"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # Create audit_logs if it doesn't exist (portable SQLAlchemy path)
    inspector = sa.inspect(bind)
    if not inspector.has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("org_id", sa.Integer, nullable=True, index=True),
            sa.Column("user_id", sa.Integer, nullable=True, index=True),
            sa.Column("action", sa.String(128), nullable=False),
            sa.Column("entity", sa.String(128), nullable=True),
            sa.Column("entity_id", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # PG-only RLS
    if bind.dialect.name != "postgresql":
        return

    op.execute(sa.text("""
    DO $plpgsql$
    DECLARE
      tbl TEXT;
    BEGIN
      FOR tbl IN SELECT unnest(ARRAY['audit_logs']) LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);

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

    if bind.dialect.name == "postgresql":
        op.execute(sa.text("""
        DO $plpgsql$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = current_schema() AND tablename = 'audit_logs' AND policyname = 'org_rls'
          ) THEN
            DROP POLICY org_rls ON audit_logs;
          END IF;
        END
        $plpgsql$;
        """))

    inspector = sa.inspect(bind)
    if inspector.has_table("audit_logs"):
        op.drop_table("audit_logs")
