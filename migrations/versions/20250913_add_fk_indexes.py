"""add fk indexes safely (sqlite + postgres)"""

from alembic import op
import sqlalchemy as sa

# --- revision IDs (leave these exactly as they are in your file)
revision = "20250913_add_fk_indexes"
down_revision = "g1h2i3j4k5l"
branch_labels = None
depends_on = None
# ---------------------------------------------------------------


def _insp(bind):
    return sa.inspect(bind)


def _has_table(bind, name: str) -> bool:
    try:
        return _insp(bind).has_table(name)
    except Exception:
        return False


def _columns(bind, table: str):
    try:
        return {c["name"] for c in _insp(bind).get_columns(table)}
    except Exception:
        return set()


def _indexes(bind, table: str):
    try:
        return {i["name"] for i in _insp(bind).get_indexes(table)}
    except Exception:
        return set()


def _fk_index_targets(bind):
    """
    Build targets automatically:
      - every FK column in every table
      - plus 'org_id' and 'status' if present
    This avoids hard-coding and works even if some columns don't exist in dev DB.
    """
    insp = _insp(bind)
    targets = set()

    # Add all FK constrained columns
    for table in insp.get_table_names():
        try:
            for fk in insp.get_foreign_keys(table):
                for col in fk.get("constrained_columns", []) or []:
                    targets.add((table, col))
        except Exception:
            # ignore tables SQLite can't introspect during batch ops
            pass

    # Add extra helpful columns if present
    for table in insp.get_table_names():
        cols = _columns(bind, table)
        for extra in ("org_id", "status"):
            if extra in cols:
                targets.add((table, extra))

    return sorted(targets)


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    insp = _insp(bind)

    for table, column in _fk_index_targets(bind):
        # skip if table/column missing
        if not _has_table(bind, table):
            continue
        if column not in _columns(bind, table):
            continue

        idx_name = f"idx_{table}_{column}"
        if idx_name in _indexes(bind, table):
            continue  # already exists

        # Create index safely on both dialects
        if dialect == "postgresql":
            op.execute(sa.text(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{table}" ("{column}")'))
        else:
            # SQLite doesn't support IF NOT EXISTS for CREATE INDEX via SQLAlchemy text in older combos
            op.create_index(idx_name, table, [column])


def downgrade():
    bind = op.get_bind()

    for table, column in _fk_index_targets(bind):
        if not _has_table(bind, table):
            continue
        idx_name = f"idx_{table}_{column}"
        if idx_name in _indexes(bind, table):
            op.drop_index(idx_name, table_name=table)
