"""Database bootstrap and seed helper using SQLAlchemy."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime

import pyotp
from argon2 import PasswordHasher
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    insert,
    select,
    text,
    inspect,
)
from sqlalchemy.engine import Engine

from db import get_engine


ph = PasswordHasher(
    time_cost=int(os.environ.get("ARGON2_TIME_COST", "3")),
    memory_cost=int(os.environ.get("ARGON2_MEMORY_COST", "65536")),
    parallelism=int(os.environ.get("ARGON2_PARALLELISM", "2")),
)


def hash_password(password: str) -> str:
    return ph.hash(password)


metadata = MetaData()

organizations = Table(
    "organizations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True, nullable=False),
)

regions_cities = Table(
    "regions_cities",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("region", String, nullable=False),
    Column("city", String, nullable=False),
)

tender_types = Table(
    "tender_types",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("type_name", String, unique=True, nullable=False),
)

roles = Table(
    "roles",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("org_id", Integer, nullable=False),
    Column("name", String, nullable=False),
    Column("description", String),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_type", String),
    Column("username", String, unique=True, nullable=False),
    Column("password_hash", String),
    Column("mfa_secret", String),
    Column("permissions", String),
    Column("approved_by_ceo", Boolean),
    Column("role", String),
    Column("last_password_change", DateTime),
)


def _table_exists(engine: Engine, name: str) -> bool:
    return inspect(engine).has_table(name)


def init_db() -> None:
    """Bootstrap a fresh/local DB so the app can import without errors."""

    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Alembic upgrade: OK")
    except FileNotFoundError:
        print("Alembic upgrade skipped or failed.")
    except subprocess.CalledProcessError:
        print("Alembic upgrade failed; continuing with SQLAlchemy models.")

    engine = get_engine()
    metadata.create_all(engine)

    with engine.begin() as conn:
        app_user = os.environ.get("APP_DB_USER")
        app_password = os.environ.get("APP_DB_PASSWORD")
        if app_user and app_password and engine.dialect.name.startswith("postgres"):
            conn.execute(
                text(
                    "DO $$BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :role) "
                    "THEN CREATE ROLE \"{}\" LOGIN PASSWORD :pwd; END IF; END$$;".format(
                        app_user
                    )
                ),
                {"role": app_user, "pwd": app_password},
            )

        regions_cities_data = [
            ("Amhara", "Bahir Dar"),
            ("Amhara", "Gondar"),
            ("Afar", "Semera"),
            ("Benishangul-Gumuz", "Asosa"),
            ("Gambela", "Gambela"),
            ("Harari", "Harar"),
            ("Oromia", "Adama"),
            ("Oromia", "Jimma"),
            ("Sidama", "Hawassa"),
            ("Somali", "Jijiga"),
            ("South West Ethiopia Peoples Region", "Bonga"),
            ("Southern Nations, Nationalities, and Peoples Region", "Arba Minch"),
            ("Tigray", "Mekelle"),
            ("Addis Ababa", "Addis Ababa"),
            ("Dire Dawa", "Dire Dawa"),
        ]
        if _table_exists(engine, "regions_cities"):
            conn.execute(
                insert(regions_cities).prefix_with("OR IGNORE"),
                [{"region": r, "city": c} for r, c in regions_cities_data],
            )

        if _table_exists(engine, "tender_types"):
            for ttype in ("EGP Portal", "Paper Tender", "NGO/UN Portal Tender"):
                conn.execute(
                    insert(tender_types).prefix_with("OR IGNORE"),
                    {"type_name": ttype},
                )

        default_org_name = os.environ.get("DEFAULT_ORG_NAME", "Default Org")
        if _table_exists(engine, "organizations"):
            conn.execute(
                insert(organizations).prefix_with("OR IGNORE"),
                {"name": default_org_name},
            )
            org_id = conn.execute(
                select(organizations.c.id).where(organizations.c.name == default_org_name)
            ).scalar()
        else:
            org_id = None

        if org_id and _table_exists(engine, "roles"):
            exists = conn.execute(
                select(roles.c.id)
                .where(roles.c.org_id == org_id)
                .where(roles.c.name == "Admin")
            ).first()
            if not exists:
                conn.execute(
                    insert(roles),
                    {
                        "org_id": org_id,
                        "name": "Admin",
                        "description": "Full platform access",
                    },
                )

        seed_demo = os.environ.get("SEED_DEMO_DATA") == "1"
        if (
            seed_demo
            and _table_exists(engine, "users")
            and os.environ.get("ENV") != "production"
        ):
            admin_username = os.environ.get("ADMIN_USERNAME")
            admin_password = os.environ.get("ADMIN_PASSWORD")
            if not admin_username or not admin_password:
                raise RuntimeError(
                    "ADMIN_USERNAME and ADMIN_PASSWORD required when SEED_DEMO_DATA=1"
                )
            password_hash = hash_password(admin_password)
            admin_secret = pyotp.random_base32()
            conn.execute(
                insert(users).prefix_with("OR IGNORE"),
                {
                    "user_type": "employee",
                    "username": admin_username,
                    "password_hash": password_hash,
                    "mfa_secret": admin_secret,
                    "permissions": "add_report,view_orders,user_management,add_inventory,receive_inventory,inventory_out,inventory_report,add_tender,tenders_list,tenders_report,put_order,maintenance_request,maintenance_status,maintenance_followup,maintenance_report",
                    "approved_by_ceo": True,
                    "role": "Admin",
                    "last_password_change": datetime.now(),
                },
            )
            print(f"Seeded admin {admin_username} with MFA secret: {admin_secret}")

            admin_phones = ["0946423021", "0984707070", "0969111144"]
            employee_phones = [
                "0969351111",
                "0969361111",
                "0969371111",
                "0969381111",
                "0969161111",
                "0923804931",
                "0911183488",
            ]
            for phone in admin_phones:
                password_hash = hash_password(phone)
                secret = pyotp.random_base32()
                conn.execute(
                    insert(users).prefix_with("OR IGNORE"),
                    {
                        "user_type": "employee",
                        "username": phone,
                        "password_hash": password_hash,
                        "mfa_secret": secret,
                        "permissions": "add_report,view_orders,user_management,add_inventory,receive_inventory,inventory_out,inventory_report,add_tender,tenders_list,tenders_report,put_order,maintenance_request,maintenance_status,maintenance_followup,maintenance_report",
                        "approved_by_ceo": True,
                        "role": "Admin",
                        "last_password_change": datetime.now(),
                    },
                )
                print(f"Seeded admin {phone} with MFA secret: {secret}")
            for phone in employee_phones:
                password_hash = hash_password(phone)
                secret = pyotp.random_base32()
                conn.execute(
                    insert(users).prefix_with("OR IGNORE"),
                    {
                        "user_type": "employee",
                        "username": phone,
                        "password_hash": password_hash,
                        "mfa_secret": secret,
                        "permissions": "add_report,put_order,view_orders",
                        "approved_by_ceo": True,
                        "role": "Sales Rep",
                        "last_password_change": datetime.now(),
                    },
                )
        elif seed_demo:
            print("SEED_DEMO_DATA ignored in production environment")

        for table in ("orders", "tenders", "inventory", "audit_logs"):
            if _table_exists(engine, table):
                conn.execute(
                    text(
                        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS org_id INTEGER REFERENCES organizations(id)"
                    )
                )
                conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
                conn.execute(text(f"DROP POLICY IF EXISTS org_rls ON {table}"))
                conn.execute(
                    text(
                        "CREATE POLICY org_rls ON {} "
                        "USING (org_id = current_setting('erp.org_id')::INTEGER) "
                        "WITH CHECK (org_id = current_setting('erp.org_id')::INTEGER)".format(
                            table
                        )
                    )
                )

    print("Database initialized / schema ensured successfully.")


if __name__ == "__main__":
    init_db()

