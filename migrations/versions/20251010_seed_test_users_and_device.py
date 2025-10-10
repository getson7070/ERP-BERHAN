"""seed test users and device allowlist (idempotent)

Revision ID: 20251010_seed_test_users_and_device
Revises: 
Create Date: 2025-10-10 20:10:00.000000

"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text
from werkzeug.security import generate_password_hash


# revision identifiers, used by Alembic.
revision = "20251010_seed_test_users_and_device"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) Ensure columns exist on users with proper defaults
    # is_active
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'is_active'
            ) THEN
                ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
            END IF;
        END$$;
    """))

    # user_type (NOT NULL) – default to role if empty, then set default
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'user_type'
            ) THEN
                ALTER TABLE users ADD COLUMN user_type VARCHAR(50);
                -- Backfill from role if present
                UPDATE users SET user_type = COALESCE(user_type, role);
                ALTER TABLE users ALTER COLUMN user_type SET NOT NULL;
            END IF;
        END$$;
    """))

    # mfa_enabled (NOT NULL DEFAULT FALSE)
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'mfa_enabled'
            ) THEN
                ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN;
                UPDATE users SET mfa_enabled = FALSE WHERE mfa_enabled IS NULL;
                ALTER TABLE users ALTER COLUMN mfa_enabled SET NOT NULL;
                ALTER TABLE users ALTER COLUMN mfa_enabled SET DEFAULT FALSE;
            END IF;
        END$$;
    """))

    # 2) Create device_authorizations if missing
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS device_authorizations (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(64) NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            allowed BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_device_user UNIQUE (device_id, user_id)
        );
    """))

    # 3) Upsert test users (email unique)
    users = [
        # (display_username, email, role/user_type, password)
        ("client",    "client@local",    "client",   "client123"),
        ("admin",     "admin@local",     "admin",    "admin123"),
        ("employee1", "employee1@local", "employee", "employee123"),
    ]

    upsert_sql = text("""
        INSERT INTO users (email, role, user_type, password_hash, is_active, mfa_enabled)
        VALUES (:email, :role, :user_type, :pwhash, TRUE, FALSE)
        ON CONFLICT (email) DO UPDATE SET
            role          = EXCLUDED.role,
            user_type     = EXCLUDED.user_type,
            password_hash = EXCLUDED.password_hash,
            is_active     = TRUE,
            mfa_enabled   = FALSE
        RETURNING id;
    """)

    inserted_ids = {}
    for _, email, role, pwd in users:
        pwhash = generate_password_hash(pwd, method="scrypt")
        res = conn.execute(upsert_sql, {
            "email": email,
            "role": role,
            "user_type": role,   # keep user_type aligned with role for now
            "pwhash": pwhash,
        })
        inserted_ids[email] = res.scalar_one()

    # 4) Seed device allowlist for admin (so all three logins activate on that device)
    admin_id = inserted_ids["admin@local"]

    # Your PC device id and the serial you shared
    admin_devices = [
        "FEDC930F-8533-44C7-8A27-4753FE57DAB8",
        "53995/04QU01214",
    ]

    for did in admin_devices:
        conn.execute(text("""
            INSERT INTO device_authorizations (device_id, user_id, allowed)
            VALUES (:did, :uid, TRUE)
            ON CONFLICT (device_id, user_id) DO UPDATE SET allowed = TRUE;
        """), {"did": did, "uid": admin_id})

    # Optional: if you want an employee-only device that enables client+employee but not admin
    # uncomment this block and set a known device id.
    # employee_only_device = "SOME-EMPLOYEE-ONLY-ID"
    # employee_id = inserted_ids["employee1@local"]
    # conn.execute(text("""
    #     INSERT INTO device_authorizations (device_id, user_id, allowed)
    #     VALUES (:did, :uid, TRUE)
    #     ON CONFLICT (device_id, user_id) DO UPDATE SET allowed = TRUE;
    # """), {"did": employee_only_device, "uid": employee_id})


def downgrade() -> None:
    # Keep downgrade conservative: we won’t drop columns or tables that may be in use.
    pass
