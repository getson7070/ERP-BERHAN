"""add fk indexes"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250913_add_fk_indexes"
down_revision = "g1h2i3j4k5l"
branch_labels = None
depends_on = None


TABLE_COLS = [
    ("orders", "org_id"),
    ("orders", "client_id"),
    ("tenders", "org_id"),
    ("inventory", "org_id"),
    ("audit_logs", "org_id"),
]


def upgrade():
    for tbl, col in TABLE_COLS:
        op.execute(f"CREATE INDEX IF NOT EXISTS idx_{tbl}_{col} ON {tbl} ({col})")


def downgrade():
    for tbl, col in TABLE_COLS:
        op.execute(f"DROP INDEX IF EXISTS idx_{tbl}_{col}")
