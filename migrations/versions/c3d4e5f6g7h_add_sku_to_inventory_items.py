"""add sku field to inventory_items (dialect-safe)"""

from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = "c3d4e5f6g7h"
down_revision = "7b8c9d0e1f2"
branch_labels = None
depends_on = None


def _has_table(insp, table_name: str, schema=None) -> bool:
    try:
        return insp.has_table(table_name, schema=schema)
    except TypeError:
        # Some dialects/versions don’t accept schema kwarg in has_table
        return insp.has_table(table_name)


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    table = "inventory_items"
    schema = None  # rely on default search_path on Postgres; fine on SQLite

    # If the table doesn't exist yet (e.g., on a partial install), just skip.
    if not _has_table(insp, table, schema=schema):
        return

    existing_cols = {c["name"] for c in insp.get_columns(table, schema=schema)}
    existing_indexes = {ix["name"] for ix in insp.get_indexes(table, schema=schema) or []}

    # Add column if missing
    if "sku" not in existing_cols:
        with op.batch_alter_table(table, schema=schema) as batch:
            batch.add_column(sa.Column("sku", sa.String(length=64), nullable=True))

    # Create a non-unique index on sku if it's not already there
    if "ix_inventory_items_sku" not in existing_indexes:
        op.create_index("ix_inventory_items_sku", table, ["sku"], unique=False, schema=schema)


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    table = "inventory_items"
    schema = None

    if not _has_table(insp, table, schema=schema):
        return

    existing_cols = {c["name"] for c in insp.get_columns(table, schema=schema)}
    existing_indexes = {ix["name"] for ix in insp.get_indexes(table, schema=schema) or []}

    if "ix_inventory_items_sku" in existing_indexes:
        op.drop_index("ix_inventory_items_sku", table_name=table, schema=schema)

    if "sku" in existing_cols:
        with op.batch_alter_table(table, schema=schema) as batch:
            batch.drop_column("sku")
