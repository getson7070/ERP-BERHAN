"""add award tracking fields to tenders (idempotent)

This migration is resilient to reruns and partially-applied schemas.
- Adds `tenders.awarded_to` only if missing.
- You can extend the same guarded pattern for any additional award fields.

"""

from alembic import op
import sqlalchemy as sa

# ---- Alembic identifiers (KEEP THESE CORRECT) ----
revision = "3d4e5f6g7h8i"
down_revision = "2b3c4d5e6f7a"
branch_labels = None
depends_on = None


def _has_table(insp, name: str) -> bool:
    return insp.has_table(name)


def _col_names(insp, table: str) -> set[str]:
    return {c["name"] for c in insp.get_columns(table)}


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not _has_table(insp, "tenders"):
        raise RuntimeError("Table 'tenders' not found; cannot apply award fields.")

    cols = _col_names(insp, "tenders")

    # Batch mode keeps Postgres/SQLite happy during ALTERs
    with op.batch_alter_table("tenders") as batch:
        # --- awarded_to ---
        if "awarded_to" not in cols:
            batch.add_column(sa.Column("awarded_to", sa.String(), nullable=True))

        # If your original migration also added more award fields, repeat the guard:
        # if "awarded_on" not in cols:
        #     batch.add_column(sa.Column("awarded_on", sa.Date(), nullable=True))
        # if "award_amount" not in cols:
        #     batch.add_column(sa.Column("award_amount", sa.Numeric(), nullable=True))
        # if "award_notes" not in cols:
        #     batch.add_column(sa.Column("award_notes", sa.Text(), nullable=True))


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not _has_table(insp, "tenders"):
        return

    cols = _col_names(insp, "tenders")

    with op.batch_alter_table("tenders") as batch:
        if "awarded_to" in cols:
            try:
                batch.drop_column("awarded_to")
            except Exception:
                # tolerate repeated downgrades
                pass

        # Repeat the same guarded drops if you added more fields:
        # for c in ("awarded_on", "award_amount", "award_notes"):
        #     if c in cols:
        #         try:
        #             batch.drop_column(c)
        #         except Exception:
        #             pass
