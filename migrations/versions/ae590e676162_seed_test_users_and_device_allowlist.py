"""seed test users and device allowlist

Revision ID: ae590e676162
Revises: cf161230ed7f   # <- keep as your current head
Create Date: 2025-10-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "ae590e676162"
down_revision = "cf161230ed7f"
branch_labels = None
depends_on = None

TEST_DEVICE = "FEDC930F-8533-44C7-8A27-4753FE57DAB8"

# Werkzeug-compatible password hashes
HASH_CLIENT   = "pbkdf2:sha256:260000$1715242873b8c9d7adb7957596dd42f2$235387770d194bfc97cc67bbe2e5eb428e5d27bbe2b126cfaeb2aa72475fe89b"   # client123
HASH_ADMIN    = "pbkdf2:sha256:260000$e354db7490032ee3169fe8b6f582f638$f90b68317c206a14735960b59ff4e9c3cf9d28f82df12f61f9f9ce72cf331a3b"   # admin123
HASH_EMPLOYEE = "pbkdf2:sha256:260000$7a1672e2f443088bcfd0e814ea068583$03b63084592392cdfd5b6de62c2a02b08a66482ccf6a0f27a1c17e4c1a1c6b9a"   # employee123

def _ensure_device_table():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "device_authorizations" in insp.get_table_names():
        return
    op.create_table(
        "device_authorizations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("device_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("allowed", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("device_id", "user_id", name="uq_device_user"),
    )

def _col_exists(table_cols, name):
    return any(c["name"] == name for c in table_cols)

def upgrade():
    bind = op.get_bind()
    _ensure_device_table()

    # Discover user table shape
    insp = sa.inspect(bind)
    user_cols = insp.get_columns("users")
    has_email = _col_exists(user_cols, "email")
    has_username = _col_exists(user_cols, "username")
    has_role = _col_exists(user_cols, "role")
    has_is_active = _col_exists(user_cols, "is_active")
    has_password_hash = _col_exists(user_cols, "password_hash")

    if not has_password_hash:
        # Try common alternative name
        has_password = _col_exists(user_cols, "password")
        pw_field = "password" if has_password else "password_hash"
    else:
        pw_field = "password_hash"

    # Build rows matching your request (username must be exactly as asked)
    rows = [
        dict(username="client",    email="client@seed.local",    role="client",    pwh=HASH_CLIENT),
        dict(username="admin",     email="admin@seed.local",     role="admin",     pwh=HASH_ADMIN),
        dict(username="employee1", email="employee1@seed.local", role="employee",  pwh=HASH_EMPLOYEE),
    ]

    for r in rows:
        # Decide identifier: prefer username if column exists; else use email
        ident_field = "username" if has_username else ("email" if has_email else None)
        if ident_field is None:
            raise RuntimeError("users table has neither 'username' nor 'email'")

        ident_value = r[ident_field]

        # Prepare insert/update column list safely
        cols = []
        vals = {}
        if has_username:   cols.append("username");   vals["username"] = r["username"]
        if has_email:      cols.append("email");      vals["email"]    = r["email"]
        if has_role:       cols.append("role");       vals["role"]     = r["role"]
        if has_is_active:  cols.append("is_active");  vals["is_active"]= True
        cols.append(pw_field);                        vals[pw_field]   = r["pwh"]

        # Build INSERT ... ON CONFLICT by whichever identifier we have
        insert_cols = ", ".join(cols + ["created_at"])
        insert_vals = ", ".join([f":{c}" for c in cols] + ["now()"])
        set_clause = ", ".join([f"{c}=EXCLUDED.{c}" for c in cols])

        sql = f"""
        INSERT INTO users ({insert_cols})
        VALUES ({insert_vals})
        ON CONFLICT ({ident_field}) DO UPDATE
        SET {set_clause}
        """
        bind.execute(text(sql), vals)

    # Fetch ids
    id_rows = bind.execute(text("""
        SELECT id, COALESCE(username, email) AS ident
        FROM users
        WHERE (username IN ('client','admin','employee1')
               OR email IN ('client@seed.local','admin@seed.local','employee1@seed.local'))
    """)).mappings().all()

    # Upsert device allow rules
    for rec in id_rows:
        bind.execute(text("""
            INSERT INTO device_authorizations (device_id, user_id, allowed, created_at)
            VALUES (:device_id, :user_id, true, now())
            ON CONFLICT ON CONSTRAINT uq_device_user DO UPDATE
            SET allowed = true
        """), dict(device_id=TEST_DEVICE, user_id=rec["id"]))

def downgrade():
    # Keep users; dropping allow-list table only if it exists
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "device_authorizations" in insp.get_table_names():
        op.drop_table("device_authorizations")
