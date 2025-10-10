"""add award tracking fields to tenders (idempotent, Postgres-safe)

Resilient to reruns and partially-applied schemas:
- Adds awarded_to only if missing.
- Copy the guarded pattern if you later add more award fields.
"""

from alembic import op
import sqlalchemy as sa

# ---- Alembic identifiers (KEEP THESE CORRECT) ----
revision = "3d4e5f6g7h8i"
down_revision = "2b3c4d5e6f7a"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("tenders"):
        raise RuntimeError("Table 'tenders' not found; cannot apply award fields.")

    cols = {c["name"] for c in insp.get_columns("tenders")}

    # Prefer inspector-guarded batch operations so Alembic can autogenerate diffs later
    with op.batch_alter_table("tenders") as batch:
        if "awarded_to" not in cols:
            batch.add_column(sa.Column("awarded_to", sa.String(), nullable=True))

    # Harden against concurrent/legacy runs: ensure column exists via IF NOT EXISTS (no-op if already there)
    op.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS awarded_to VARCHAR;")

    # Example for future fields (uncomment if your original migration added them):
    # with op.batch_alter_table("tenders") as batch:
    #     if "awarded_on" not in cols:
    #         batch.add_column(sa.Column("awarded_on", sa.Date(), nullable=True))
    #     if "award_amount" not in cols:
    #         batch.add_column(sa.Column("award_amount", sa.Numeric(), nullable=True))


def downgrade():
    # Guarded drops so repeated downgrades won't crash
    op.execute("ALTER TABLE IF EXISTS tenders DROP COLUMN IF EXISTS awarded_to;")
    # op.execute("ALTER TABLE IF EXISTS tenders DROP COLUMN IF EXISTS awarded_on;")
    # op.execute("ALTER TABLE IF EXISTS tenders DROP COLUMN IF EXISTS award_amount;")
