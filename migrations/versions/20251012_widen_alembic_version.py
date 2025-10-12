from alembic import op
import sqlalchemy as sa

revision = "20251012_widen_ver"
down_revision = "20251010_seed_test_users_dev"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    bind.exec_driver_sql("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema='public'
          AND table_name='alembic_version'
          AND column_name='version_num'
          AND (character_maximum_length IS NULL OR character_maximum_length < 64)
      ) THEN
        ALTER TABLE public.alembic_version
        ALTER COLUMN version_num TYPE varchar(64);
      END IF;
    END $$;
    """)

def downgrade():
    # Only safe if you never wrote >32-char IDs after widening
    bind = op.get_bind()
    bind.exec_driver_sql("""
      ALTER TABLE public.alembic_version
      ALTER COLUMN version_num TYPE varchar(32);
    """)
