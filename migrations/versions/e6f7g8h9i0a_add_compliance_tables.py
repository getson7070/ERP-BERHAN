# migrations/versions/e6f7g8h9i0a_add_compliance_tables.py
from alembic import op
import sqlalchemy as sa

revision = "e6f7g8h9i0a"
down_revision = "20251010_seed_test_users_and_device"   # keep your actual chain here
branch_labels = None
depends_on = None

def _table_exists(bind, name, schema="public"):
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)

def _columns(bind, table, schema="public"):
    insp = sa.inspect(bind)
    return {c["name"] for c in insp.get_columns(table, schema=schema)}

def upgrade():
    bind = op.get_bind()
    cols = set()

    if not _table_exists(bind, "electronic_signatures"):
        op.create_table(
            "electronic_signatures",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, nullable=False),
            sa.Column("intent", sa.String(255), nullable=False),
            sa.Column("signed_at", sa.DateTime, nullable=False),
            sa.Column("prev_hash", sa.String(64)),
            sa.Column("signature_hash", sa.String(64), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )
    else:
        cols = _columns(bind, "electronic_signatures")
        if "prev_hash" not in cols:
            op.add_column("electronic_signatures", sa.Column("prev_hash", sa.String(64)))
        if "signature_hash" not in cols:
            op.add_column("electronic_signatures", sa.Column("signature_hash", sa.String(64), nullable=False))

def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "electronic_signatures"):
        op.drop_table("electronic_signatures")
