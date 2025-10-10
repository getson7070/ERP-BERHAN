"""seed test users and device allowlist

Revision ID: ae590e676162
Revises: cf161230ed7f
Create Date: 2025-10-10 10:25:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# -----------------------------------------------------------------------------
# Alembic identifiers
# -----------------------------------------------------------------------------
revision = "ae590e676162"
down_revision = "cf161230ed7f"
branch_labels = None
depends_on = None

# -----------------------------------------------------------------------------
# --- schema knobs ---
#
# If your "users" table uses different column names,
# adjust these names to match your schema.
# -----------------------------------------------------------------------------
USERS_TABLE = "users"
USER_EMAIL_COL = "email"
USER_ROLE_COL = "role"
USER_PWHASH_COL = "password_hash"
USER_ISACTIVE_COL = "is_active"

DEV_AUTH_TABLE = "device_authorizations"
DEV_DEVICE_COL = "device_id"
DEV_USERID_COL = "user_id"
DEV_ROLE_COL = "role"
DEV_ALLOWED_COL = "allowed"

# Test users (email, role, plain_password)
TEST_USERS = [
    ("client@local", "client", "client123"),
    ("employee1@local", "employee", "employee123"),
    ("admin@local", "admin", "admin123"),
]

# Devices to allow for 'admin' (enables all tiles in your gating logic)
ADMIN_DEVICES = [
    "FEDC930F-8533-44C7-8A27-4753FE57DAB8",  # your Windows PC
    "53995/04QU01214",                       # your Xiaomi tablet (serial)
]


def _hash_password(plain: str) -> str:
    """
    Generate a PBKDF2-SHA256 hash using Werkzeug (present in your requirements).
    We do it inside the migration so secrets are never stored in plain text.
    """
    try:
        from werkzeug.security import generate_password_hash

        return generate_password_hash(plain)  # defaults PBKDF2:sha256
    except Exception:
        # Fallback to a deterministic (but still salted) hash if Werkzeug isn't importable
        # (shouldn't happen on Render given your requirements).
        import hashlib, os, base64

        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
        return f"sha256${salt}${hashlib.sha256((salt + plain).encode()).hexdigest()}"


def upgrade() -> None:
    conn = op.get_bind()

    # -------------------------------------------------------------------------
    # 1) Seed / upsert users
    # -------------------------------------------------------------------------
    upsert_user_sql = text(
        f"""
        INSERT INTO {USERS_TABLE} ({USER_EMAIL_COL}, {USER_ROLE_COL}, {USER_PWHASH_COL}, {USER_ISACTIVE_COL})
        VALUES (:email, :role, :pwhash, TRUE)
        ON CONFLICT ({USER_EMAIL_COL})
        DO UPDATE SET
            {USER_ROLE_COL} = EXCLUDED.{USER_ROLE_COL},
            {USER_PWHASH_COL} = EXCLUDED.{USER_PWHASH_COL},
            {USER_ISACTIVE_COL} = TRUE
        """
    )

    for email, role, plain_pwd in TEST_USERS:
        conn.execute(
            upsert_user_sql,
            {"email": email.lower(), "role": role, "pwhash": _hash_password(plain_pwd)},
        )

    # -------------------------------------------------------------------------
    # 2) Global device allowlist (role='admin' means show all tiles on device)
    #    We store as a "global" device rule by keeping user_id NULL.
    #    If your table has a UNIQUE constraint on (device_id, role) or
    #    (device_id, user_id, role), the ON CONFLICT below will keep this idempotent.
    # -------------------------------------------------------------------------
    # Figure out which unique constraint exists; we try the common (device_id, role).
    # If your table is different, adjust ON CONFLICT accordingly.
    allow_sql = text(
        f"""
        INSERT INTO {DEV_AUTH_TABLE} ({DEV_DEVICE_COL}, {DEV_USERID_COL}, {DEV_ROLE_COL}, {DEV_ALLOWED_COL})
        VALUES (:device, NULL, 'admin', TRUE)
        ON CONFLICT ({DEV_DEVICE_COL}, {DEV_ROLE_COL})
        DO UPDATE SET {DEV_ALLOWED_COL} = TRUE
        """
    )

    for device in ADMIN_DEVICES:
        conn.execute(allow_sql, {"device": device})

    # -------------------------------------------------------------------------
    # 3) (Optional) also map each device to the concrete admin user,
    #    in case your app checks per-user device rows first.
    # -------------------------------------------------------------------------
    admin_id = conn.execute(
        text(
            f"SELECT id FROM {USERS_TABLE} WHERE {USER_EMAIL_COL} = :email LIMIT 1"
        ),
        {"email": "admin@local"},
    ).scalar()

    if admin_id is not None:
        allow_per_user_sql = text(
            f"""
            INSERT INTO {DEV_AUTH_TABLE} ({DEV_DEVICE_COL}, {DEV_USERID_COL}, {DEV_ROLE_COL}, {DEV_ALLOWED_COL})
            VALUES (:device, :uid, 'admin', TRUE)
            ON CONFLICT ({DEV_DEVICE_COL}, {DEV_USERID_COL}, {DEV_ROLE_COL})
            DO UPDATE SET {DEV_ALLOWED_COL} = TRUE
            """
        )
        for device in ADMIN_DEVICES:
            conn.execute(allow_per_user_sql, {"device": device, "uid": admin_id})


def downgrade() -> None:
    conn = op.get_bind()

    # Remove device allowlist rows we added
    conn.execute(
        text(
            f"""
            DELETE FROM {DEV_AUTH_TABLE}
            WHERE {DEV_DEVICE_COL} = ANY(:devices)
              AND ({DEV_ROLE_COL} = 'admin')
            """
        ),
        {"devices": ADMIN_DEVICES},
    )

    # Remove the test users (in case you want to roll back cleanly)
    conn.execute(
        text(
            f"""
            DELETE FROM {USERS_TABLE}
            WHERE {USER_EMAIL_COL} = ANY(:emails)
            """
        ),
        {"emails": [u[0] for u in TEST_USERS]},
    )
