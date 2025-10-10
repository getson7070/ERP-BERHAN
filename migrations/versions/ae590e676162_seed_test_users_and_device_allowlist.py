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

    # ---- Make sure required columns/tables exist ---------------------------
    # Add is_active / role if missing.
    op.execute("""
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
    """)
    op.execute("""
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS role VARCHAR(50) NOT NULL DEFAULT 'client';
    """)

    # Your schema already has user_type and it is NOT NULL.
    # Ensure it has a DEFAULT so inserts that omit it won't fail,
    # and normalize any NULLs just in case of older data.
    op.execute("""
        ALTER TABLE users
            ALTER COLUMN user_type SET DEFAULT 'client';
    """)
    # If the column exists and somehow has NULLs (older data), normalize:
    op.execute("""
        UPDATE users
           SET user_type = 'client'
         WHERE user_type IS NULL;
    """)

    # Ensure device_authorizations table exists.
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
    # Map role -> user_type. If you use different terms in your app, adjust here.
    users = [
        ("client@local",    "client",   "client",   "client123"),
        ("admin@local",     "admin",    "admin",    "admin123"),
        ("employee1@local", "employee", "employee", "employee123"),
    ]

    upsert_user_sql = text("""
        INSERT INTO users (email, role, user_type, password_hash, is_active)
        VALUES (:email, :role, :user_type, :pwhash, TRUE)
        ON CONFLICT (email) DO UPDATE SET
            role          = EXCLUDED.role,
            user_type     = EXCLUDED.user_type,
            password_hash = EXCLUDED.password_hash,
            is_active     = TRUE
        RETURNING id;
    """)

    email_to_id = {}
    for email, role, user_type, plain in users:
        pwhash = generate_password_hash(plain)
        res = conn.execute(upsert_user_sql, {
            "email": email,
            "role": role,
            "user_type": user_type,
            "pwhash": pwhash,
        })
        user_id = res.scalar()
        email_to_id[email] = user_id

    # ---- Seed device allowlist ---------------------------------------------
    # Devices you specified
    win_pc = "FEDC930F-8533-44C7-8A27-4753FE57DAB8"
    android_serial = "53995/04QU01214"

    upsert_device_sql = text("""
        INSERT INTO device_authorizations (user_id, device_id, allowed)
        VALUES (:user_id, :device_id, TRUE)
        ON CONFLICT (user_id, device_id) DO UPDATE SET
            allowed = EXCLUDED.allowed;
    """)

    admin_id = email_to_id.get("admin@local")
    if admin_id:
        conn.execute(upsert_device_sql, {"user_id": admin_id, "device_id": win_pc})
        conn.execute(upsert_device_sql, {"user_id": admin_id, "device_id": android_serial})

    employee_id = email_to_id.get("employee1@local")
    if employee_id:
        conn.execute(upsert_device_sql, {"user_id": employee_id, "device_id": win_pc})

    # Client login remains public (no device row needed).


def downgrade() -> None:
    conn = op.get_bind()

    # Remove seeded devices
    conn.execute(text("""
        DELETE FROM device_authorizations
        WHERE device_id IN (
            'FEDC930F-8533-44C7-8A27-4753FE57DAB8',
            '53995/04QU01214'
        );
    """))

    # Remove seeded users (only if these are test accounts)
    conn.execute(text("""
        DELETE FROM users
        WHERE email IN ('client@local','admin@local','employee1@local');
    """))

    # Keep structure changes; removing defaults/columns here
    # could break real data. Uncomment if you truly need to revert:
    # op.execute("ALTER TABLE users ALTER COLUMN user_type DROP DEFAULT;")
    # op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_active;")
    # op.execute("ALTER TABLE users DROP COLUMN IF EXISTS role;")
    # op.execute("DROP TABLE IF EXISTS device_authorizations;")
