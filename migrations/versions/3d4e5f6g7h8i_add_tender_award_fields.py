"""add award tracking fields to tenders (idempotent, Postgres-safe)"""

from alembic import op
import sqlalchemy as sa

# ----- Alembic identifiers (KEEP THESE CORRECT) -----
revision = "3d4e5f6g7h8i"
down_revision = "2b3c4d5e6f7a"
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL with IF NOT EXISTS to avoid DuplicateColumn on reruns
    # Primary field that caused the failure:
    op.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS awarded_to VARCHAR;")

    # If your original migration added more award fields, guard them the same way:
    # op.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS awarded_on DATE;")
    # op.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS award_amount NUMERIC;")
    # op.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS award_notes TEXT;")
    # (leave them commented out unless your code expects them)


def downgrade():
    # Guarded drops so repeated downgrades won't crash
    op.execute("ALTER TABLE IF EXISTS tenders DROP COLUMN IF EXISTS awarded_to;")
    # op.execute("ALTER TABLE IF EXISTS tenders DROP COLUMN IF EXISTS awarded_on;")
    # op.execute("ALTER TABLE IF EXISTS tenders DROP COLUMN IF EXISTS award_amount;")
    # op.execute("ALTER TABLE IF EXISTS tenders DROP COLUMN IF EXISTS award_notes;")
