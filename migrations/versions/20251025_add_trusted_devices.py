from alembic import op
import sqlalchemy as sa

revision = "20251025_trusted_devices"
down_revision = "a1b2c3d4e5f6"   # keep your existing branch point
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Ensure minimal 'users' exists so FK won't fail
    if "users" not in insp.get_table_names():
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(length=255), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    # Create trusted_devices once
    if "trusted_devices" not in insp.get_table_names():
        op.create_table(
            "trusted_devices",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("device_fingerprint", sa.String(length=255), nullable=False),
            sa.Column("ua", sa.String(length=512)),
            sa.Column("ip", sa.String(length=64)),
            sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("expires_at", sa.DateTime(timezone=True)),
            sa.UniqueConstraint("user_id", "device_fingerprint", name="uq_user_device"),
        )

def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "trusted_devices" in insp.get_table_names():
        op.drop_table("trusted_devices")
    # Intentionally do not drop 'users'