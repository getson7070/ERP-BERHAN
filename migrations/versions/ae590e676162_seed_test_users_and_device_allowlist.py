"""seed test users and device allowlist

Revision ID: ae590e676162
Revises: cf161230ed7f
Create Date: 2025-10-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ae590e676162"
down_revision = None  # or set to your real previous revision id
branch_labels = None
depends_on = None


def _pg_guard_add_column(table: str, col_def_sql: str, col_name: str):
    """
    Add a column to a Postgres table only if it doesn't already exist.
    col_def_sql: e.g. "is_active BOOLEAN NOT NULL DEFAULT TRUE"
    """
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = :tbl AND column_name = :col
                ) THEN
                    EXECUTE 'ALTER TABLE {table} ADD COLUMN {col_def_sql}';
                END IF;
            END$$;
            """
        ),
        {"tbl": table, "col": col_name},
    )


def _pg_create_table_if_not_exists():
    # device_authorizations table, IF NOT EXISTS
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS device_authorizations (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(64) NOT NULL,
            user_id INTEGER NOT NULL,
            allowed BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            CONSTRAINT uq_device_user UNIQUE (device_id, user_id),
            CONSTRAINT fk_device_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """
    )
    # optional index
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_device_authorizations_device_id ON device_authorizations (device_id);"
    )


def _upsert_user(conn, email: str, role: str, user_type: str, password_hash: str):
    # Ensure we provide all NOT NULL columns that exist in your DB
    # Adjust column names if your users table differs.
    upsert_sql = sa.text(
        """
        INSERT INTO users (email, role, user_type, password_hash, is_active, mfa_enabled)
        VALUES (:email, :role, :user_type, :pwhash, TRUE, FALSE)
        ON CONFLICT (email) DO UPDATE SET
            role          = EXCLUDED.role,
            user_type     = EXCLUDED.user_type,
            password_hash = EXCLUDED.password_hash,
            is_active     = TRUE
        RETURNING id;
        """
    )
    res = conn.execute(
        upsert_sql,
        {"email": email, "role": role, "user_type": user_type, "pwhash": password_hash},
    )
    return res.scalar_one()


def _allow_device(conn, user_id: int, device_id: str):
    conn.execute(
        sa.text(
            """
            INSERT INTO device_authorizations (device_id, user_id, allowed)
            VALUES (:device_id, :user_id, TRUE)
            ON CONFLICT (device_id, user_id) DO UPDATE SET allowed = TRUE;
            """
        ),
        {"device_id": device_id, "user_id": user_id},
    )


def upgrade() -> None:
    # 1) Harden users table for the seed:
    # These guards are safe even if the columns already exist.
    _pg_guard_add_column("users", "is_active BOOLEAN NOT NULL DEFAULT TRUE", "is_active")
    _pg_guard_add_column("users", "mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE", "mfa_enabled")
    _pg_guard_add_column("users", "user_type VARCHAR(50) NOT NULL DEFAULT 'client'", "user_type")

    # 2) Ensure device_authorizations exists
    _pg_create_table_if_not_exists()

    # 3) Seed users and device allowlist
    # Password hashes created with Werkzeug's generate_password_hash(..., method="scrypt")
    client_pw = "scrypt:32768:8:1$CLIENT$5a5e6cfb..."      # <-- replace with your real hash
    admin_pw = "scrypt:32768:8:1$ADMIN$2e2a17b9..."        # <-- replace with your real hash
    employee_pw = "scrypt:32768:8:1$EMP$9c1d62aa..."       # <-- replace with your real hash

    # If you don't have the exact hashes handy, you can swap in pbkdf2:sha256 hashes you already used.

    FEDC = "FEDC930F-8533-44C7-8A27-4753FE57DAB8"
    SERIAL = "53995/04QU01214"

    conn = op.get_bind()

    # client
    client_id = _upsert_user(
        conn,
        email="client@local",
        role="client",
        user_type="client",
        password_hash=client_pw,
    )
    # admin
    admin_id = _upsert_user(
        conn,
        email="admin@local",
        role="admin",
        user_type="admin",
        password_hash=admin_pw,
    )
    # employee
    employee_id = _upsert_user(
        conn,
        email="employee1@local",
        role="employee",
        user_type="employee",
        password_hash=employee_pw,
    )

    # allow devices
    # Admin: both the PC Device Id and the Serial are allowed
    _allow_device(conn, admin_id, FEDC)
    _allow_device(conn, admin_id, SERIAL)

    # Employee: allow only FEDC
    _allow_device(conn, employee_id, FEDC)

    # Client: public — no device record required


def downgrade() -> None:
    # Make the seed reversible-ish: delete our specific seeds only.
    conn = op.get_bind()
    for email in ("client@local", "admin@local", "employee1@local"):
        conn.execute(sa.text("DELETE FROM device_authorizations WHERE user_id IN (SELECT id FROM users WHERE email=:e)"), {"e": email})
        conn.execute(sa.text("DELETE FROM users WHERE email=:e"), {"e": email})
