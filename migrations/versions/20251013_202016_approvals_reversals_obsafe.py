
"""Add approvals/reversals columns safely (Postgres IF EXISTS/IF NOT EXISTS)
Revision ID: appr_rev_20251013_202016
Revises: 
Create Date: 2025-10-13T20:20:16.998184
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "appr_rev_20251013_202016"
down_revision = None  # this revision is a branch root; will be merged by 20251014_merge_heads_stable
branch_labels = None
depends_on = None

TABLES = ["journal_entries", "invoices", "bills", "grn", "deliveries"]

def upgrade():
    for t in TABLES:
        op.execute(f"""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{t}') THEN
                ALTER TABLE IF EXISTS {t}
                    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Draft',
                    ADD COLUMN IF NOT EXISTS approved_by UUID NULL,
                    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE NULL,
                    ADD COLUMN IF NOT EXISTS reversed_of UUID NULL,
                    ADD COLUMN IF NOT EXISTS reversed_by UUID NULL,
                    ADD COLUMN IF NOT EXISTS reversed_at TIMESTAMP WITH TIME ZONE NULL;
            END IF;
        END $$;
        """)

def downgrade():
    for t in TABLES:
        op.execute(f"""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '{t}' AND column_name='status') THEN
                ALTER TABLE IF EXISTS {t}
                    DROP COLUMN IF EXISTS status,
                    DROP COLUMN IF EXISTS approved_by,
                    DROP COLUMN IF EXISTS approved_at,
                    DROP COLUMN IF EXISTS reversed_of,
                    DROP COLUMN IF EXISTS reversed_by,
                    DROP COLUMN IF EXISTS reversed_at;
            END IF;
        END $$;
        """)
