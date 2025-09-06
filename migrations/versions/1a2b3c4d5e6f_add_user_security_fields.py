"""add security fields to users and password_resets table

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2024-09-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def _table_exists(conn, name: str) -> bool:
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()

# revision identifiers, used by Alembic.
revision = "1a2b3c4d5e6f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if not _table_exists(conn, "users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.String(), nullable=False, unique=True),
            sa.Column("password", sa.String(), nullable=False),
            sa.Column("org_id", sa.Integer, nullable=True),
            sa.Column("failed_attempts", sa.Integer(), server_default="0"),
            sa.Column("account_locked", sa.Boolean(), server_default="0"),
            sa.Column("last_password_change", sa.DateTime(), nullable=True),
        )
    else:
        cols = [col["name"] for col in inspector.get_columns("users")]
        if "failed_attempts" not in cols:
            op.add_column(
                "users", sa.Column("failed_attempts", sa.Integer(), server_default="0")
            )
        if "account_locked" not in cols:
            op.add_column(
                "users", sa.Column("account_locked", sa.Boolean(), server_default="0")
            )
        if "last_password_change" not in cols:
            op.add_column(
                "users", sa.Column("last_password_change", sa.DateTime(), nullable=True)
            )

    for base in ("tenders", "orders", "inventory", "inventory_items"):
        if not _table_exists(conn, base):
            op.create_table(base, sa.Column("id", sa.Integer, primary_key=True))

    if not _table_exists(conn, "password_resets"):
        op.create_table(
            "password_resets",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")
            ),
            sa.Column("token", sa.String(length=255), nullable=False, unique=True),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
        )


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if _table_exists(conn, "password_resets"):
        op.drop_table("password_resets")
    if _table_exists(conn, "users"):
        cols = [col["name"] for col in inspector.get_columns("users")]
        if "last_password_change" in cols:
            op.drop_column("users", "last_password_change")
        if "account_locked" in cols:
            op.drop_column("users", "account_locked")
        if "failed_attempts" in cols:
            op.drop_column("users", "failed_attempts")
