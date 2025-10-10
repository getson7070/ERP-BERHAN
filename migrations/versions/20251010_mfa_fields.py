# migrations/versions/20251010_mfa_fields.py
"""Add MFA fields safely"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# !!! CHANGE THESE TWO TO MATCH YOUR TREE !!!
revision = "20251010_mfa_fields"
down_revision = "cf161230ed7f"
branch_labels = None
depends_on = None

def _has_column(conn, table, column) -> bool:
    insp = Inspector.from_engine(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols

def upgrade():
    conn = op.get_bind()
    if not _has_column(conn, "users", "mfa_secret"):
        op.add_column("users", sa.Column("mfa_secret", sa.String(length=64), nullable=True))
    if not _has_column(conn, "users", "mfa_enabled"):
        op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))

def downgrade():
    conn = op.get_bind()
    if _has_column(conn, "users", "mfa_enabled"):
        op.drop_column("users", "mfa_enabled")
    if _has_column(conn, "users", "mfa_secret"):
        op.drop_column("users", "mfa_secret")
