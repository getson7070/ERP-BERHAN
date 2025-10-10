"""add mfa fields and lockout hygiene"""
from alembic import op
import sqlalchemy as sa

revision = "20251010_mfa"
down_revision = None  # set to your latest if you have chain
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("mfa_secret", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("mfa_recovery", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("failed_logins", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("last_failed_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(), nullable=True))
    op.create_index("ix_users_created_at", "users", ["created_at"])
    op.create_index("ix_users_role_active", "users", ["role", "is_active"])

def downgrade():
    op.drop_index("ix_users_role_active", table_name="users")
    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "last_failed_at")
    op.drop_column("users", "failed_logins")
    op.drop_column("users", "mfa_recovery")
    op.drop_column("users", "mfa_secret")
    op.drop_column("users", "mfa_enabled")
