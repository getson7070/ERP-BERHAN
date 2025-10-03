from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6g"
down_revision = "b1c2d3e4f5g6"
branch_labels = None
depends_on = None

def _has_table(bind, name: str) -> bool:
    try:
        insp = sa.inspect(bind)
        return insp.has_table(name)
    except Exception:
        return False

def _has_column(bind, table: str, column: str) -> bool:
    try:
        insp = sa.inspect(bind)
        cols = [c["name"] for c in insp.get_columns(table)]
        return column in cols
    except Exception:
        return False

def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    # On SQLite dev DB, invoices may not exist (PG-only in earlier revision).
    if not _has_table(bind, "invoices"):
        # no-op safely on SQLite / any DB without invoices
        return

    # Add column only if it doesn't already exist
    if not _has_column(bind, "invoices", "delete_after"):
        # Use batch_alter for SQLite compatibility
        with op.batch_alter_table("invoices") as batch:
            batch.add_column(sa.Column("delete_after", sa.DateTime(), nullable=True))

def downgrade():
    bind = op.get_bind()
    if _has_table(bind, "invoices") and _has_column(bind, "invoices", "delete_after"):
        with op.batch_alter_table("invoices") as batch:
            batch.drop_column("delete_after")
