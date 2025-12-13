"""
Seed baseline data (SEED ONLY).

- Alembic migrations own schema creation.
- This script only inserts baseline org/roles/permissions/admin if missing.
- It must be safe to run multiple times.
"""

from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from db import get_engine


DEFAULT_ORG_TIN = os.getenv("DEFAULT_ORG_TIN", "0000000000")
DEFAULT_ORG_NAME = os.getenv("DEFAULT_ORG_NAME", "Berhan Pharma PLC")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@berhanpharma.com")
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_TIN = os.getenv("DEFAULT_ADMIN_TIN", "0000000000")


def _now() -> str:
    return datetime.utcnow().isoformat()


def seed_baseline(engine: Engine) -> None:
    with engine.begin() as conn:
        # If migrations haven't been applied, do not crash-loop.
        try:
            conn.execute(text("SELECT 1 FROM organizations LIMIT 1"))
        except ProgrammingError as e:
            msg = str(e).lower()
            if "does not exist" in msg and "organizations" in msg:
                print("[init_db] organizations table missing. Skipping seed (migrations not applied).")
                return
            raise

        # 1) Organization
        org_id = conn.execute(
            text("SELECT id FROM organizations WHERE tin = :tin"),
            {"tin": DEFAULT_ORG_TIN},
        ).scalar()

        if not org_id:
            conn.execute(
                text(
                    """
                    INSERT INTO organizations (tin, name, email, phone, address_text, is_active, created_at, updated_at)
                    VALUES (:tin, :name, NULL, NULL, NULL, TRUE, NOW(), NOW())
                    """
                ),
                {"tin": DEFAULT_ORG_TIN, "name": DEFAULT_ORG_NAME},
            )
            org_id = conn.execute(
                text("SELECT id FROM organizations WHERE tin = :tin"),
                {"tin": DEFAULT_ORG_TIN},
            ).scalar()

        # 2) Permissions catalog (examples; extend as your modules grow)
        perms = [
            ("auth.login", "auth", "Login access"),
            ("users.read", "users", "View users"),
            ("users.manage", "users", "Create/update users"),
            ("roles.manage", "rbac", "Create/update roles"),
            ("permissions.assign", "rbac", "Assign permissions"),
            ("tenders.manage", "tenders", "Create/update tenders"),
            ("discounts.approve", "sales", "Approve discounts"),
        ]
        for code, module, desc in perms:
            conn.execute(
                text(
                    """
                    INSERT INTO permissions (code, module, description, created_at)
                    VALUES (:code, :module, :desc, NOW())
                    ON CONFLICT (code) DO NOTHING
                    """
                ),
                {"code": code, "module": module, "desc": desc},
            )

        # 3) System roles (org_id NULL means “global/system role”)
        roles = [
            ("admin", "Full system access + oversight + approvals", True),
            ("storekeeper", "Inventory operations", True),
            ("sales_rep", "Sales operations", True),
            ("engineer", "Maintenance/service operations", True),
            ("tender_clerk", "Tender registration & tracking", True),
        ]
        for name, desc, is_system in roles:
            conn.execute(
                text(
                    """
                    INSERT INTO roles (org_id, name, description, is_system, created_at)
                    VALUES (NULL, :name, :desc, :is_system, NOW())
                    ON CONFLICT (org_id, name) DO NOTHING
                    """
                ),
                {"name": name, "desc": desc, "is_system": bool(is_system)},
            )

        # 4) Admin user (note: password handling is managed elsewhere in your app)
        admin_id = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": DEFAULT_ADMIN_EMAIL},
        ).scalar()

        if not admin_id:
            conn.execute(
                text(
                    """
                    INSERT INTO users
                      (org_id, user_type, tin, full_name, username, email, phone, position,
                       telegram_chat_id, password_hash, is_active, created_at, updated_at)
                    VALUES
                      (:org_id, 'admin', :tin, 'System Admin', :username, :email, NULL, 'Admin',
                       NULL, NULL, TRUE, NOW(), NOW())
                    """
                ),
                {
                    "org_id": int(org_id),
                    "tin": DEFAULT_ADMIN_TIN,
                    "username": DEFAULT_ADMIN_USERNAME,
                    "email": DEFAULT_ADMIN_EMAIL,
                },
            )
            admin_id = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": DEFAULT_ADMIN_EMAIL},
            ).scalar()

        # 5) Assign admin role
        admin_role_id = conn.execute(
            text("SELECT id FROM roles WHERE org_id IS NULL AND name = 'admin'"),
        ).scalar()

        if admin_role_id and admin_id:
            conn.execute(
                text(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES (:user_id, :role_id)
                    ON CONFLICT (user_id, role_id) DO NOTHING
                    """
                ),
                {"user_id": int(admin_id), "role_id": int(admin_role_id)},
            )

        print(f"[init_db] Seed OK at {_now()} | org_id={org_id} admin_id={admin_id}")


def main() -> None:
    engine = get_engine()
    seed_baseline(engine)


if __name__ == "__main__":
    main()
