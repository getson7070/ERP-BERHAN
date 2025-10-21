"""Database bootstrap utility using SQLAlchemy.

This script initialises the database schema and seed data for local
or test environments. It replaces earlier raw SQL usage with
SQLAlchemy metadata and connection helpers to improve maintainability
and safety.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path

import pyotp
try:
    from argon2 import PasswordHasher
except Exception:
    import hashlib
    class PasswordHasher:
        def hash(self, pw: str) -> str:
            return hashlib.sha256(pw.encode("utf-8")).hexdigest()
        def verify(self, h: str, pw: str) -> bool:
            return self.hash(pw) == h
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    select,
    text,
)
from sqlalchemy.engine import Connection

from db import get_engine


ph = PasswordHasher(
    time_cost=int(os.environ.get("ARGON2_TIME_COST", "3")),
    memory_cost=int(os.environ.get("ARGON2_MEMORY_COST", "65536")),
    parallelism=int(os.environ.get("ARGON2_PARALLELISM", "2")),
)

metadata = MetaData()

regions = Table(
    "regions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True, nullable=False),
)

cities = Table(
    "cities",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("region_id", ForeignKey("regions.id")),
    Column("name", String, nullable=False),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_type", String),
    Column("username", String, unique=True),
    Column("password_hash", String),
    Column("mfa_secret", String),
    Column("permissions", String),
    Column("approved_by_ceo", Boolean),
    Column("role", String),
    Column("last_password_change", DateTime),
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


def hash_password(password: str) -> str:
    return ph.hash(password)


def _table_exists(conn: Connection, table: str) -> bool:
    if conn.dialect.name.startswith("sqlite"):
        row = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
            {"n": table},
        ).first()
        return row is not None
    return conn.execute(
        text("SELECT to_regclass(:t)"), {"t": f"public.{table}"}
    ).scalar() is not None


def _insert_ignore(conn: Connection, table: Table, values: dict) -> None:
    ins = table.insert().values(**values)
    if conn.dialect.name.startswith("sqlite"):
        ins = ins.prefix_with("OR IGNORE")
    else:
        ins = ins.prefix_with("ON CONFLICT DO NOTHING")
    conn.execute(ins)


def _reset_schema() -> None:
    engine = get_engine()
    dialect = engine.dialect.name

    if dialect.startswith("sqlite"):
        database = engine.url.database
        # Dispose the engine before touching on-disk files so SQLite
        # releases any outstanding locks from the failed migration
        # attempt.
        engine.dispose()
        if database and database != ":memory:":
            Path(database).unlink(missing_ok=True)
        else:  # in-memory database â€“ drop all tables instead
            with engine.begin() as conn:
                tables = conn.execute(
                    text(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                ).all()
                for (table_name,) in tables:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
        return

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


def init_db() -> None:
    """Bootstrap a fresh/local DB so the app can import without errors."""

    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Alembic upgrade: OK")
    except FileNotFoundError:
        print("Alembic upgrade skipped or failed.")
    except subprocess.CalledProcessError:
        print("Alembic upgrade failed; resetting schema and retrying...")
        _reset_schema()
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Alembic upgrade: OK")

    engine = get_engine()
    metadata.create_all(engine)
    with engine.begin() as conn:

        # Seed regions and cities if empty
        if conn.execute(select(regions.c.id)).first() is None:
            region_ids: dict[str, int] = {}
            for region_name, city_name in regions_cities_data:
                region_id = region_ids.get(region_name)
                if region_id is None:
                    res = conn.execute(regions.insert().values(name=region_name))
                    region_id = int(res.inserted_primary_key[0])
                    region_ids[region_name] = region_id
                conn.execute(cities.insert().values(region_id=region_id, name=city_name))

        seed_demo = os.environ.get("SEED_DEMO_DATA") == "1" and os.environ.get(
            "FLASK_ENV", "development"
        ) != "production"
        if seed_demo:
            admin_username = os.environ.get("ADMIN_USERNAME")
            admin_password = os.environ.get("ADMIN_PASSWORD")
            if not admin_username or not admin_password:
                raise RuntimeError(
                    "ADMIN_USERNAME and ADMIN_PASSWORD required when SEED_DEMO_DATA=1"
                )
            password_hash = hash_password(admin_password)
            admin_secret = pyotp.random_base32()
            _insert_ignore(
                conn,
                users,
                dict(
                    user_type="employee",
                    username=admin_username,
                    password_hash=password_hash,
                    mfa_secret=admin_secret,
                    permissions="add_report,view_orders,user_management,add_inventory,receive_inventory,inventory_out,inventory_report,add_tender,tenders_list,tenders_report,put_order,maintenance_request,maintenance_status,maintenance_followup,maintenance_report",
                    approved_by_ceo=True,
                    role="Admin",
                    last_password_change=datetime.now(),
                ),
            )
            print(f"Seeded admin {admin_username} with MFA secret: {admin_secret}")
            for phone in admin_phones:
                password_hash = hash_password(phone)
                secret = pyotp.random_base32()
                _insert_ignore(
                    conn,
                    users,
                    dict(
                        user_type="employee",
                        username=phone,
                        password_hash=password_hash,
                        mfa_secret=secret,
                        permissions="add_report,view_orders,user_management,add_inventory,receive_inventory,inventory_out,inventory_report,add_tender,tenders_list,tenders_report,put_order,maintenance_request,maintenance_status,maintenance_followup,maintenance_report",
                        approved_by_ceo=True,
                        role="Admin",
                        last_password_change=datetime.now(),
                    ),
                )
                print(f"Seeded admin {phone} with MFA secret: {secret}")
            for phone in employee_phones:
                password_hash = hash_password(phone)
                secret = pyotp.random_base32()
                _insert_ignore(
                    conn,
                    users,
                    dict(
                        user_type="employee",
                        username=phone,
                        password_hash=password_hash,
                        mfa_secret=secret,
                        permissions="add_report,put_order,view_orders",
                        approved_by_ceo=True,
                        role="Sales Rep",
                        last_password_change=datetime.now(),
                    ),
                )
        elif seed_demo:
            print("SEED_DEMO_DATA ignored in production environment")

        for table in ("orders", "tenders", "inventory", "audit_logs"):
            if _table_exists(conn, table):
                conn.execute(
                    text(
                        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS org_id INTEGER REFERENCES organizations(id)"
                    )
                )
                conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
                conn.execute(text(f"DROP POLICY IF EXISTS org_rls ON {table}"))
                conn.execute(
                    text(
                        f"CREATE POLICY org_rls ON {table} "
                        "USING (org_id = current_setting('erp.org_id')::INTEGER) "
                        "WITH CHECK (org_id = current_setting('erp.org_id')::INTEGER)"
                    )
                )

    print("Database initialized / schema ensured successfully.")


if __name__ == "__main__":  # pragma: no cover
    init_db()



# ---- helper hashing API (stable across backends) ----
try:
    ph  # reuse whatever PasswordHasher/shim is already configured above
except NameError:  # last-resort shim if something changes unexpectedly
    try:
        from argon2 import PasswordHasher as _Argon2PH
        ph = _Argon2PH(time_cost=2, memory_cost=51200, parallelism=2, hash_len=32, salt_len=16)
    except Exception:
        from werkzeug.security import generate_password_hash, check_password_hash
        class _PHShim:
            def hash(self, pw: str) -> str:
                return generate_password_hash(pw, method="pbkdf2:sha256", salt_length=16)
            def verify(self, hashed: str, pw: str) -> bool:
                try:
                    return check_password_hash(hashed, pw)
                except Exception:
                    return False
        ph = _PHShim()

def hash_password(pw: str) -> str:
    return ph.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, pw)  # argon2 style
    except TypeError:
        # just in case a shim expects (pw, hashed)
        return ph.verify(pw, hashed)
    except Exception:
        return False
# ---- /helper hashing API ----


