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


def _ensure_column(table: str, col: str, ddl_to_add: str) -> None:
    """Create a column if it doesn't exist."""
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                  FROM information_schema.columns
                 WHERE table_name = '{table}'
                   AND column_name = '{col}'
            ) THEN
                ALTER TABLE {table} ADD COLUMN {ddl_to_add};
            END IF;
        END$$;
        """
    )


def _ensure_default_and_not_null(table: str, col: str, default_sql: str, fill_value_sql: str) -> None:
    """
    Ensure a column has a DEFAULT and is NOT NULL.

    default_sql:   e.g. "FALSE" or "0" or "'client'"
    fill_value_sql same literal to fill existing NULLs.
    """
    # Set DEFAULT
    op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} SET DEFAULT {default_sql};")
    # Normalize NULLs
    op.execute(f"UPDATE {table} SET {col} = {fill_value_sql} WHERE {col} IS NULL;")
    # Enforce NOT NULL
    op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} SET NOT NULL;")


def upgrade() -> None:
    conn = op.get_bind()

    # ----------------------------------------------------------------------
    # Ensure required columns/tables exist and have safe defaults
    # ----------------------------------------------------------------------
    _ensure_column("users", "is_active", "BOOLEAN NOT NULL DEFAULT TRUE")
    _ensure_column("users", "role", "VARCHAR(50) NOT NULL DEFAULT 'client'")
    _ensure_column("users", "user_type", "VARCHAR(50) NOT NULL DEFAULT 'client'")
    _ensure_column("users", "mfa_enabled", "BOOLEAN NOT NULL DEFAULT FALSE")
    _ensure_column("users", "failed_login_attempts", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column("users", "is_locked", "BOOLEAN NOT NULL DEFAULT FALSE")

    # In case the columns already existed but lacked defaults or NOT NULL, make that true now.
    _ensure_default_and_not_null("users", "is_active", "TRUE", "TRUE")
    _ensure_default_and_not_null("users", "role", "'client'", "'client'")
    _ensure_default_and_not_null("users", "user_type", "'client'", "'client'")
    _ensure_default_and_not_null("users", "mfa_enabled", "FALSE", "FALSE")
    _ensure_default_and_not_null("users", "failed_login_attempts", "0", "0")
    _ensure_default_and_not_null("users", "is_locked", "FALSE", "FALSE")

    # device_authorizations (for per-user allowlist)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS device_authorizations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            device_id VARCHAR(128) NOT NULL,
            allowed BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (user_id, device_id)
        );
        """
    )

    # ----------------------------------------------------------------------
    # Seed test users with explicit values for NOT NULL columns
    # ----------------------------------------------------------------------
    users = [
        ("client@local",    "client",   "client",   "client123",   False, 0, False),
        ("admin@local",     "admin",    "admin",    "admin123",    False, 0, False),
        ("employee1@local", "employee", "employee", "employee123", False, 0, False),
    ]

    upsert_user_sql = text(
        """
        INSERT INTO users (
            email, role, user_type, password_hash,
            is_active, mfa_enabled, failed_login_attempts, is_locked
        )
        VALUES (
            :email, :role, :user_type, :pwhash,
            TRUE, :mfa_enabled, :failed_login_attempts, :is_locked
        )
        ON CONFLICT (email) DO UPDATE SET
            role                   = EXCLUDED.role,
            user_type              = EXCLUDED.user_type,
            password_hash          = EXCLUDED.password_hash,
            is_active              = TRUE,
            mfa_enabled            = EXCLUDED.mfa_enabled,
            failed_login_attempts  = EXCLUDED.failed_login_attempts,
            is_locked              = EXCLUDED.is_locked
        RETURNING id;
        """
    )

    email_to_id = {}
    for email, role, user_type, plain, mfa_enabled, failed_attempts, is_locked in users:
        pwhash = generate_password_hash(plain)
        res = conn.execute(
            upsert_user_sql,
            dict(
                email=email,
                role=role,
                user_type=user_type,
                pwhash=pwhash,
                mfa_enabled=mfa_enabled,
                failed_login_attempts=failed_attempts,
                is_locked=is_locked,
            ),
        )
        email_to_id[email] = res.scalar()

    # ----------------------------------------------------------------------
    # Seed device allowlist
    # ----------------------------------------------------------------------
    win_pc = "FEDC930F-8533-44C7-8A27-4753FE57DAB8"  # Windows PC
    android_serial = "53995/04QU01214"               # Android tablet serial

    upsert_device_sql = text(
        """
        INSERT INTO device_authorizations (user_id, device_id, allowed)
        VALUES (:user_id, :device_id, TRUE)
        ON CONFLICT (user_id, device_id) DO UPDATE SET
            allowed = EXCLUDED.allowed;
        """
    )

    admin_id = email_to_id.get("admin@local")
    if admin_id:
        conn.execute(upsert_device_sql, {"user_id": admin_id, "device_id": win_pc})
        conn.execute(upsert_device_sql, {"user_id": admin_id, "device_id": android_serial})

    employee_id = email_to_id.get("employee1@local")
    if employee_id:
        conn.execute(upsert_device_sql, {"user_id": employee_id, "device_id": win_pc})
        # (Optionally allow the Android for employee as well; leave out if admin-only.)

    # Client login is public (no device row needed).


def downgrade() -> None:
    conn = op.get_bind()

    # Remove seeded devices
    conn.execute(
        text(
            """
            DELETE FROM device_authorizations
             WHERE device_id IN (
                'FEDC930F-8533-44C7-8A27-4753FE57DAB8',
                '53995/04QU01214'
             );
            """
        )
    )

    # Remove seeded users (only if these are test accounts)
    conn.execute(
        text(
            """
            DELETE FROM users
             WHERE email IN ('client@local','admin@local','employee1@local');
            """
        )
    )

    # Keep structure changes; rolling these back can break real data.
    # If you truly need to revert, you can DROP defaults/columns here.
