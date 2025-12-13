"""
Seed baseline data (SAFE + IDEMPOTENT).

- Alembic owns schema creation
- This script ONLY inserts baseline data
- Explicitly provides UUIDs for users
"""

import os
import uuid

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from db import get_engine


DEFAULT_ORG_TIN = os.getenv("DEFAULT_ORG_TIN", "0000000000")
DEFAULT_ORG_NAME = os.getenv("DEFAULT_ORG_NAME", "Berhan Pharma PLC")

DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@berhanpharma.com")
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_TIN = os.getenv("DEFAULT_ADMIN_TIN", "0000000000")


def seed_baseline(engine: Engine) -> None:
    with engine.begin() as conn:

        # Ensure migrations already ran
        try:
            conn.execute(text("SELECT 1 FROM organizations LIMIT 1"))
        except ProgrammingError:
            print("[init_db] organizations table missing – migrations not applied yet")
            return

        # -------------------------------------------------
        # Organization
        # -------------------------------------------------
        org_id = conn.execute(
            text("SELECT id FROM organizations WHERE tin = :tin"),
            {"tin": DEFAULT_ORG_TIN},
        ).scalar()

        if not org_id:
            conn.execute(
                text("""
                    INSERT INTO organizations (tin, name, created_at)
                    VALUES (:tin, :name, NOW())
                    ON CONFLICT (tin) DO NOTHING
                """),
                {"tin": DEFAULT_ORG_TIN, "name": DEFAULT_ORG_NAME},
            )
            org_id = conn.execute(
                text("SELECT id FROM organizations WHERE tin = :tin"),
                {"tin": DEFAULT_ORG_TIN},
            ).scalar()

        # -------------------------------------------------
        # Admin User (EXPLICIT UUID)
        # -------------------------------------------------
        admin_exists = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": DEFAULT_ADMIN_EMAIL},
        ).scalar()

        if not admin_exists:
            conn.execute(
                text("""
                    INSERT INTO users
                      (uuid, org_id, user_type, tin, full_name,
                       username, email, is_active, created_at, updated_at)
                    VALUES
                      (:uuid, :org_id, 'admin', :tin, 'System Admin',
                       :username, :email, TRUE, NOW(), NOW())
                """),
                {
                    "uuid": str(uuid.uuid4()),
                    "org_id": org_id,
                    "tin": DEFAULT_ADMIN_TIN,
                    "username": DEFAULT_ADMIN_USERNAME,
                    "email": DEFAULT_ADMIN_EMAIL,
                },
            )

        # -------------------------------------------------
        # System Role
        # -------------------------------------------------
        conn.execute(
            text("""
                INSERT INTO roles (org_id, name, description, is_system, created_at)
                VALUES (NULL, 'admin', 'System Administrator', TRUE, NOW())
                ON CONFLICT (org_id, name) DO NOTHING
            """)
        )

        # -------------------------------------------------
        # Assign Role
        # -------------------------------------------------
        conn.execute(
            text("""
                INSERT INTO user_roles (user_id, role_id)
                SELECT u.id, r.id
                FROM users u, roles r
                WHERE u.email = :email
                  AND r.name = 'admin'
                  AND r.org_id IS NULL
                ON CONFLICT DO NOTHING
            """),
            {"email": DEFAULT_ADMIN_EMAIL},
        )

        print("[init_db] Baseline seed completed successfully")


def main() -> None:
    engine = get_engine()
    seed_baseline(engine)


if __name__ == "__main__":
    main()
