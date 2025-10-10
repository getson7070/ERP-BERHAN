"""seed test users and device allowlist (idempotent)"""

from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash

# revision identifiers, used by Alembic.
revision = "ae590e676162"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1) Ensure required user columns exist (idempotent)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='users' AND column_name='username'
        ) THEN
            ALTER TABLE users ADD COLUMN username VARCHAR(255);
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='users' AND column_name='user_type'
        ) THEN
            ALTER TABLE users ADD COLUMN user_type VARCHAR(50) NOT NULL DEFAULT 'client';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='users' AND column_name='is_active'
        ) THEN
            ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='users' AND column_name='mfa_enabled'
        ) THEN
            ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='users' AND column_name='mfa_verified'
        ) THEN
            ALTER TABLE users ADD COLUMN mfa_verified BOOLEAN NOT NULL DEFAULT FALSE;
        END IF;
    END$$;
    """)

    # 2) Create device_authorizations table if not exists
    op.execute("""
    CREATE TABLE IF NOT EXISTS device_authorizations (
        id SERIAL PRIMARY KEY,
        device_id VARCHAR(64) NOT NULL,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        allowed BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """)

    # unique constraint if not exists
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_device_user'
        ) THEN
            ALTER TABLE device_authorizations
            ADD CONSTRAINT uq_device_user UNIQUE (device_id, user_id);
        END IF;
    END$$;
    """)

    # 3) Upsert users with all required fields
    def upsert_user(username, email, role, user_type, password_plain):
        pwhash = generate_password_hash(password_plain)
        res = conn.execute(sa.text("""
            INSERT INTO users (username, email, role, user_type, password_hash, is_active, mfa_enabled, mfa_verified)
            VALUES (:username, :email, :role, :user_type, :pwhash, TRUE, FALSE, FALSE)
            ON CONFLICT (email) DO UPDATE SET
                username      = EXCLUDED.username,
                role          = EXCLUDED.role,
                user_type     = EXCLUDED.user_type,
                password_hash = EXCLUDED.password_hash,
                is_active     = TRUE,
                mfa_enabled   = FALSE,
                mfa_verified  = FALSE
            RETURNING id;
        """), {"username": username, "email": email, "role": role, "user_type": user_type, "pwhash": pwhash})
        return res.scalar_one()

    client_id   = upsert_user("client",    "client@local",    "client",   "client",   "client123")
    admin_id    = upsert_user("admin",     "admin@local",     "admin",    "admin",    "admin123")
    employee_id = upsert_user("employee1", "employee1@local", "employee", "employee", "employee123")

    # 4) Seed device allowlist
    def allow(device_id, user_id, allowed=True):
        conn.execute(sa.text("""
            INSERT INTO device_authorizations (device_id, user_id, allowed)
            VALUES (:device_id, :user_id, :allowed)
            ON CONFLICT (device_id, user_id) DO UPDATE SET
                allowed = EXCLUDED.allowed;
        """), {"device_id": device_id, "user_id": user_id, "allowed": allowed})

    # Your PC Device Id
    allow("FEDC930F-8533-44C7-8A27-4753FE57DAB8", admin_id, True)      # admin device → all roles allowed by policy
    allow("FEDC930F-8533-44C7-8A27-4753FE57DAB8", employee_id, True)   # let employee on same device too (optional)
    allow("FEDC930F-8533-44C7-8A27-4753FE57DAB8", client_id, True)     # client is public anyway

    # Android serial you provided
    allow("53995/04QU01214", admin_id, True)
    allow("53995/04QU01214", employee_id, True)
    allow("53995/04QU01214", client_id, True)


def downgrade():
    # keep seeded data; do not drop
    pass
