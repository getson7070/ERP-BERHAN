from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f7"
down_revision = "9e0f1a2b3c4d"
branch_labels = None
depends_on = None

def _pg(conn):
    return conn.dialect.name == "postgresql"

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Create table if missing
    if not insp.has_table("user_dashboards", schema="public"):
        op.create_table(
            "user_dashboards",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, nullable=False),
            sa.Column("layout", sa.Text, nullable=False),
            sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()"), nullable=False),
            schema="public",
        )

    # On Postgres, ensure unique + FK constraints exist
    if _pg(bind):
        # unique(user_id)
        exists_unique = bind.exec_driver_sql("""
            SELECT 1 FROM pg_constraint
            WHERE conname = 'user_dashboards_user_id_key'
        """).first()
        if not exists_unique:
            bind.exec_driver_sql("""
                ALTER TABLE public.user_dashboards
                ADD CONSTRAINT user_dashboards_user_id_key UNIQUE (user_id)
            """)

        # fk(user_id) -> users(id)
        exists_fk = bind.exec_driver_sql("""
            SELECT 1 FROM pg_constraint
            WHERE conname = 'user_dashboards_user_id_fkey'
        """).first()
        if not exists_fk:
            bind.exec_driver_sql("""
                ALTER TABLE public.user_dashboards
                ADD CONSTRAINT user_dashboards_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES public.users (id)
            """)

def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if insp.has_table("user_dashboards", schema="public"):
        # Drop constraints if present (Postgres only)
        if bind.dialect.name == "postgresql":
            for con in ("user_dashboards_user_id_fkey", "user_dashboards_user_id_key"):
                bind.exec_driver_sql(f"""
                    DO $$ BEGIN
                    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{con}') THEN
                        ALTER TABLE public.user_dashboards DROP CONSTRAINT {con};
                    END IF;
                    END $$;
                """)
        op.drop_table("user_dashboards", schema="public")
