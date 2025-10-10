"""Add MFA fields safely (idempotent)"""

from alembic import op
import sqlalchemy as sa

# NOTE: keep your real revision IDs here
revision = "20251010_mfa_fields"
down_revision = "<PUT_YOUR_PREVIOUS_REVISION_ID_HERE>"
branch_labels = None
depends_on = None

def _has_column(bind, table, column):
    insp = sa.inspect(bind)
    return any(col["name"] == column for col in insp.get_columns(table))

def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name.lower()

    if dialect == "postgresql":
        # Use IF NOT EXISTS so re-running is safe
        op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR(64)")
        op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE")
        # Optional comment
        op.execute("COMMENT ON COLUMN users.mfa_secret IS 'TOTP seed'")
        # Remove default to keep model defaults in code authoritative
        op.execute("ALTER TABLE users ALTER COLUMN mfa_enabled DROP DEFAULT")
    else:
        # Generic fallback for sqlite/mysql/etc.
        if not _has_column(bind, "users", "mfa_secret"):
            op.add_column("users", sa.Column("mfa_secret", sa.String(length=64), nullable=True))
        if not _has_column(bind, "users", "mfa_enabled"):
            op.add_column(
                "users",
                sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            )
            # backfill + drop default
            op.execute("UPDATE users SET mfa_enabled = 0 WHERE mfa_enabled IS NULL")
            op.alter_column("users", "mfa_enabled", server_default=None)

def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name.lower()

    if dialect == "postgresql":
        op.execute("ALTER TABLE users DROP COLUMN IF EXISTS mfa_enabled")
        op.execute("ALTER TABLE users DROP COLUMN IF EXISTS mfa_secret")
    else:
        if _has_column(bind, "users", "mfa_enabled"):
            op.drop_column("users", "mfa_enabled")
        if _has_column(bind, "users", "mfa_secret"):
            op.drop_column("users", "mfa_secret")
