"""seed test users and device allowlist

Revision ID: ae590e676162
Revises: 
Create Date: 2025-10-10 10:32:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash

# revision identifiers, used by Alembic.
revision = "ae590e676162"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ---- Ensure users table has the columns we rely on ----------------------
    # Add is_active and role if they don't exist (PostgreSQL)
    op.execute("""
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
    """)
    op.execute("""
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS role VARCHAR(50) NOT NULL DEFAULT 'client';
    """)

    # ---- Ensure device_authorizations table exists --------------------------
    # This table is (user_id, device_id) unique; allowed toggles access.
    op.execute("""
        CREATE TABLE IF NOT EXISTS device_authorizations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            device_id VARCHAR(128) NOT NULL,
            allowed BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (user_id, device_id)
        );
    """)

    # ---- Seed users (UPSERT on email) --------------------------------------
    # Note: we seed with emails like client@local; if your login field accepts plain
    # "client" you can type that and we can normalize in the app to append @local.
    users = [
        ("client@local",   "client",   "client123"),
        ("admin@local",    "admin",    "admin123"),
        ("employee1@local","employee", "employee123"),
    ]

    upsert_user_sql = text("""
        INSERT INTO users (email, role, password_hash, is_active)
        VALUES (:email, :role, :pwhash, TRUE)
        ON CONFLICT (email) DO UPDATE SET
            role = EXCLUDED.role,
            password_hash = EXCLUDED.password_hash,
            is_active = TRUE
        RETURNING id;
    """)

    email_to_id = {}
    for email, role, plain in users:
        pwhash = generate_password_hash(plain)
        res = conn.execute(upsert_user_sql, {"email": email, "role": role, "pwhash": pwhash})
        user_id = res.scalar()
        email_to_id[email] = user_id

    # ---- Seed device allowlist ---------------------------------------------
    # Windows PC Device ID provided earlier:
    win_pc = "FEDC930F-8533-44C7-8A27-4753FE57DAB8"
    # Android tablet serial (you asked to allow for admin):
    android_serial = "53995/04QU01214"

    # Helper UPSERT for device_authorizations
    upsert_device_sql = text("""
        INSERT INTO device_authorizations (user_id, device_id, allowed)
        VALUES (:user_id, :device_id, TRUE)
        ON CONFLICT (user_id, device_id) DO UPDATE SET
            allowed = EXCLUDED.allowed;
    """)

    # Policy you requested:
    # - If device is allowed for admin -> all three roles activate on UI.
    # - If device is allowed only for employee -> client + employee activate.
    # - If device is not in allowlist -> only client activates (public).
    #
    # We encode that by marking both devices for the admin user.
    admin_id = email_to_id.get("admin@local")
    if admin_id:
        conn.execute(upsert_device_sql, {"user_id": admin_id, "device_id": win_pc})
        conn.execute(upsert_device_sql, {"user_id": admin_id, "device_id": android_serial})

    # Optionally allow the Windows PC for the employee too, if you want:
    employee_id = email_to_id.get("employee1@local")
    if employee_id:
        conn.execute(upsert_device_sql, {"user_id": employee_id, "device_id": win_pc})

    # And the client is public, so device list isn’t required for client.
    # (No row needed for client; your view logic should show client tile always.)


def downgrade() -> None:
    conn = op.get_bind()

    # Remove seeded device rows
    conn.execute(text("""
        DELETE FROM device_authorizations
        WHERE device_id IN (
            'FEDC930F-8533-44C7-8A27-4753FE57DAB8',
            '53995/04QU01214'
        );
    """))

    # Remove seeded users (safe if you’re only using these for testing)
    conn.execute(text("""
        DELETE FROM users
        WHERE email IN ('client@local','admin@local','employee1@local');
    """))

    # We don't drop columns or tables here to avoid breaking real data.
    # If you must revert structure too, you could:
    # op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_active;")
    # op.execute("ALTER TABLE users DROP COLUMN IF EXISTS role;")
    # op.execute("DROP TABLE IF EXISTS device_authorizations;")
