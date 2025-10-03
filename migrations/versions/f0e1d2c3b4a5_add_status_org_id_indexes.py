from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f0e1d2c3b4a5"
down_revision = "b2c3d4e5f6g"
branch_labels = None
depends_on = None

def _insp(bind):
    return sa.inspect(bind)

def _has_table(bind, name: str) -> bool:
    try:
        return _insp(bind).has_table(name)
    except Exception:
        return False

def _has_column(bind, table: str, column: str) -> bool:
    try:
        cols = {c["name"] for c in _insp(bind).get_columns(table)}
        return column in cols
    except Exception:
        return False

def _has_index(bind, table: str, name: str) -> bool:
    try:
        idxs = [i["name"] for i in _insp(bind).get_indexes(table)]
        return name in idxs
    except Exception:
        return False

def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if not _has_table(bind, "orders"):
        return

    # On SQLite dev DB, 'status' may not exist (PG schema has it). Skip safely.
    if dialect == "sqlite" and not _has_column(bind, "orders", "status"):
        # Optional: still create an index on org_id to help local testing
        if _has_column(bind, "orders", "org_id") and not _has_index(bind, "orders", "ix_orders_org_id"):
            op.create_index("ix_orders_org_id", "orders", ["org_id"])
        return

    # PG (or SQLite if both columns exist)
    if _has_column(bind, "orders", "status") and _has_column(bind, "orders", "org_id"):
        if not _has_index(bind, "orders", "ix_orders_status_org_id"):
            op.create_index("ix_orders_status_org_id", "orders", ["status", "org_id"])

def downgrade():
    bind = op.get_bind()
    if _has_table(bind, "orders"):
        if _has_index(bind, "orders", "ix_orders_status_org_id"):
            op.drop_index("ix_orders_status_org_id", table_name="orders")
        if _has_index(bind, "orders", "ix_orders_org_id"):
            op.drop_index("ix_orders_org_id", table_name="orders")
