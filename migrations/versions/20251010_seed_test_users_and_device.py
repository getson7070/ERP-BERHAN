from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = "20251010_seed_test_users_and_device"
down_revision = "cf161230ed7f"  # <-- your current head from `alembic heads`
branch_labels = None
depends_on = None

TEST_DEVICE = "FEDC930F-8533-44C7-8A27-4753FE57DAB8"

# These are werkzeug-compatible pbkdf2:sha256 hashes for your requested passwords.
# (Do NOT change these strings unless you regenerate them.)
HASH_CLIENT   = "pbkdf2:sha256:260000$1715242873b8c9d7adb7957596dd42f2$235387770d194bfc97cc67bbe2e5eb428e5d27bbe2b126cfaeb2aa72475fe89b"
HASH_ADMIN    = "pbkdf2:sha256:260000$e354db7490032ee3169fe8b6f582f638$f90b68317c206a14735960b59ff4e9c3cf9d28f82df12f61f9f9ce72cf331a3b"
HASH_EMPLOYEE = "pbkdf2:sha256:260000$7a1672e2f443088bcfd0e814ea068583$03b63084592392cdfd5b6de62c2a02b08a66482ccf6a0f27a1c17e4c1a1c6b9a"

def upgrade():
    conn = op.get_bind()

    # 1) device_authorizations (CREATE IF NOT EXISTS)
    op.create_table(
        "device_authorizations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("device_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("allowed", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("device_id", "user_id", name="uq_device_user"),
    )

    # 2) Upsert three users (client/admin/employee)
    #    Note: adjust column names if your users table differs.
    for email, role, pwhash in [
        ("client@seed.local",   "client",   HASH_CLIENT),
        ("admin@seed.local",    "admin",    HASH_ADMIN),
        ("employee1@seed.local","employee", HASH_EMPLOYEE),
    ]:
        conn.execute(sa.text("""
            INSERT INTO users (email, password_hash, role, is_active, created_at)
            VALUES (:email, :password_hash, :role, true, now())
            ON CONFLICT (email) DO UPDATE
            SET password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                is_active = true
        """), dict(email=email, password_hash=pwhash, role=role))

    # 3) Link the allowed device to all three users
    #    Fetch IDs and insert allow-list rows idempotently.
    rows = conn.execute(sa.text("""
        SELECT id, email FROM users
        WHERE email IN ('client@seed.local','admin@seed.local','employee1@seed.local')
    """)).mappings().all()

    for r in rows:
        conn.execute(sa.text("""
            INSERT INTO device_authorizations (device_id, user_id, allowed, created_at)
            VALUES (:device_id, :user_id, true, now())
            ON CONFLICT ON CONSTRAINT uq_device_user DO UPDATE
            SET allowed = true
        """), dict(device_id=TEST_DEVICE, user_id=r["id"]))

def downgrade():
    # Do not drop users on downgrade; just remove the allow-list table to be safe.
    op.drop_table("device_authorizations")
