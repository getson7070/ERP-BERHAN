"""add tender workflow columns (idempotent rewrite)

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2025-10-11

NOTE:
This version guards against re-running on databases where columns already exist.
"""

from alembic import op
import sqlalchemy as sa

revision = "2b3c4d5e6f7a"
down_revision = "1a2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("tenders")}

    # Ensure table exists before batch (some engines require guard)
    if not insp.has_table("tenders"):
        raise RuntimeError("Table 'tenders' not found")

    with op.batch_alter_table("tenders") as batch:
        # workflow_state
        if "workflow_state" not in cols:
            batch.add_column(
                sa.Column(
                    "workflow_state",
                    sa.String(),
                    nullable=False,
                    server_default="advert_registered",
                )
            )
        else:
            # Make sure it's NOT NULL and has a default; backfill nulls
            op.execute(
                "UPDATE tenders SET workflow_state='advert_registered' "
                "WHERE workflow_state IS NULL"
            )
            batch.alter_column(
                "workflow_state",
                existing_type=sa.String(),
                nullable=False,
                server_default="advert_registered",
            )

        # result
        if "result" not in cols:
            batch.add_column(sa.Column("result", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("tenders") as batch:
        if sa.inspect(op.get_bind()).has_table("tenders"):
            # Drop guarded to avoid errors if already removed
            try:
                batch.drop_column("result")
            except Exception:
                pass
            try:
                batch.drop_column("workflow_state")
            except Exception:
                pass
