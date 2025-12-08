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

from alembic.config import Config
from alembic.script import ScriptDirectory

from erp.security_hardening import safe_run, safe_call, safe_popen  # noqa: F401

import pyotp

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
    inspect,
)
from sqlalchemy.engine import Connection

from db import get_engine

# --------------------------------------------------------------------
# Password hashing – bcrypt-compatible by default
# --------------------------------------------------------------------


class _PasswordHelper:
    """Unified password helper.

    Primary path: bcrypt-based hashes (compatible with Flask-Bcrypt /
    bcrypt.checkpw and similar).

    Fallback: Werkzeug's generate_password_hash/check_password_hash
    so this script can still run even if `bcrypt` is not installed
    in some environments.
    """

    def __init__(self) -> None:
        self._mode = "bcrypt"
        self._bcrypt = None
        self._generate = None
        self._check = None

        # Try bcrypt first (preferred)
        try:
            import bcrypt  # type: ignore[import-not-found]

            self._bcrypt = bcrypt
            self._mode = "bcrypt"
        except Exception:
            # Fallback to Werkzeug hashing
            try:
                from werkzeug.security import (
                    generate_password_hash,
                    check_password_hash,
                )

                self._generate = generate_password_hash
                self._check = check_password_hash
                self._mode = "werkzeug"
            except Exception:
                # Last-resort ultra-simple shim (not recommended for real use,
                # but prevents crashes if everything else is missing).
                import hashlib

                self._mode = "sha256"
                self._generate = lambda pw: hashlib.sha256(
                    pw.encode("utf-8")
                ).hexdigest()
                self._check = (
                    lambda hashed, pw: hashed
                    == hashlib.sha256(pw.encode("utf-8")).hexdigest()
                )

    def hash(self, pw: str) -> str:
        if self._mode == "bcrypt" and self._bcrypt is not None:
            # bcrypt expects bytes; we generate a standard bcrypt string
            salt = self._bcrypt.gensalt()
            hashed = self._bcrypt.hashpw(pw.encode("utf-8"), salt)
            return hashed.decode("utf-8")

        # Werkzeug or SHA256 fallback
        return self._generate(pw)

    def verify(self, hashed: str, pw: str) -> bool:
        if self._mode == "bcrypt" and self._bcrypt is not None:
            try:
                return self._bcrypt.checkpw(
                    pw.encode("utf-8"), hashed.encode("utf-8")
                )
            except Exception:
                return False

        try:
            return bool(self._check(hashed, pw))
        except Exception:
            return False


ph = _PasswordHelper()


def hash_password(password: str) -> str:
    """Hash password using the configured helper.

    For the normal case this will produce bcrypt-style hashes compatible
    with Flask-Bcrypt / bcrypt.checkpw, so existing login code that uses
    `bcrypt.check_password_hash` will accept these values.
    """
    return ph.hash(password)


# --------------------------------------------------------------------
# SQLAlchemy table metadata for seeding
# --------------------------------------------------------------------

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

# NOTE:
# This local SQLAlchemy Table is *only* used for seeding. The real
# canonical schema is defined in Alembic migrations. That means the
# set of columns here may not be perfectly in-sync with the DB, so
# all write paths must be defensive and driven by live inspection of
# the database, not by this metadata object.
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_type", String),  # legacy; may not exist in DB
    Column("username", String, unique=True),
    Column("email", String, unique=True, nullable=False),
    Column("password_hash", String),
    Column("mfa_secret", String),  # legacy; real MFA may live elsewhere
    Column("permissions", String),
    Column("approved_by_ceo", Boolean),
    Column("role", String),
    Column("last_password_change", DateTime),
    # created_at / updated_at / is_active are added by migrations
    # and discovered dynamically via inspector.
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


# --------------------------------------------------------------------
# Helper functions for schema + seeding
# --------------------------------------------------------------------


def _table_exists(conn: Connection, table: str) -> bool:
    if conn.dialect.name.startswith("sqlite"):
        row = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
            {"n": table},
        ).first()
        return row is not None
    return (
        conn.execute(text("SELECT to_regclass(:t)"), {"t": f"public.{table}"})
        .scalar()
        is not None
    )


def _insert_ignore(conn: Connection, table: Table, values: dict) -> None:
    """Insert a row into `table` if it does not already exist.

    Defensive against schema drift:

    - Inspects the *actual* DB columns via inspector.
    - Drops any keys that do not map to real columns.
    - Fills reasonable defaults for NOT NULL columns.
    - NEVER overrides the primary key / identity column `id`.
    - Uses raw INSERT built from the live column list, avoiding
      SQLAlchemy's "unconsumed column names" issue when local
      metadata is out of sync with the DB.
    """
    inspector_obj = inspect(conn)
    columns_info = inspector_obj.get_columns(table.name)
    existing_cols = [col["name"] for col in columns_info]

    now = datetime.now()
    filtered_values: dict[str, object] = {}

    for col in columns_info:
        col_name = col["name"]

        # Never manually set primary key / identity – leave to DB sequence
        if col_name == "id":
            continue

        if col_name in values:
            val = values[col_name]
        elif not col.get("nullable", True):
            # Best-effort type detection
            try:
                py_type = col["type"].python_type
            except Exception:
                py_type = None

            if col_name == "email":
                val = f"{values.get('username', 'admin')}@berhanpharma.com"
            elif col_name == "approved_by_ceo":
                val = True
            elif col_name == "role":
                # If caller requested a role, keep it; otherwise default
                val = values.get("role", "User")
            elif col_name == "last_password_change":
                val = now
            elif col_name in ("created_at", "updated_at"):
                val = now
            elif col_name == "is_active":
                val = True
            else:
                if py_type is str:
                    val = ""
                elif py_type is bool:
                    val = False
                elif py_type is datetime:
                    val = now
                else:
                    # Fallback for ints/numerics/etc.
                    val = 0
        else:
            # Nullable and not explicitly provided – let DB default/null handle it
            continue

        filtered_values[col_name] = val

    if not filtered_values:
        return  # nothing meaningful to insert

    cols = list(filtered_values.keys())
    col_list = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(f":{c}" for c in cols)

    # Build dialect-specific SQL without using the local Table metadata,
    # so we never hit "unconsumed column names" even if metadata is stale.
    if conn.dialect.name.startswith("sqlite"):
        # SQLite: use INSERT OR IGNORE to mimic "upsert" on unique constraints
        stmt_txt = (
            f'INSERT OR IGNORE INTO "{table.name}" ({col_list}) '
            f"VALUES ({placeholders})"
        )
    else:
        # PostgreSQL: use ON CONFLICT on username when available
        stmt_txt = f'INSERT INTO "{table.name}" ({col_list}) VALUES ({placeholders})'
        if "username" in existing_cols:
            stmt_txt += ' ON CONFLICT ("username") DO NOTHING'

    stmt = text(stmt_txt)
    conn.execute(stmt, filtered_values)


def _reset_schema() -> None:
    """Drop and recreate the schema when Alembic upgrade fails."""
    engine = get_engine()
    dialect = engine.dialect.name

    if dialect.startswith("sqlite"):
        database = engine.url.database
        # Dispose the engine before touching on-disk files so SQLite
        # releases any outstanding locks from the failed migration
        # attempt.
        engine.dispose()
        if database and database != ":memory__":
            Path(database).unlink(missing_ok=True)
        else:  # in-memory database – drop all tables instead
            with engine.begin() as conn:
                tables = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                ).all()
                for (table_name,) in tables:
                    conn.execute(
                        text(f'DROP TABLE IF NOT EXISTS "{table_name}"')
                    )
        return

    # PostgreSQL path
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


def _get_migration_heads() -> list[str]:
    """Return all Alembic heads for the configured environment."""

    alembic_ini = os.getenv("ALEMBIC_INI_PATH", "alembic.ini")
    cfg = Config(alembic_ini)
    script = ScriptDirectory.from_config(cfg)
    return list(script.get_heads())


def _assert_single_migration_head(heads: list[str] | None = None) -> list[str]:
    """Fail fast when multiple heads exist to avoid restart loops.

    The caller can optionally supply ``heads`` to simplify testing; otherwise the
    heads are resolved from the Alembic environment. The returned list is
    deduplicated and sorted for readability.
    """

    resolved_heads = sorted(set(heads or _get_migration_heads()))
    if len(resolved_heads) > 1:
        formatted = ", ".join(resolved_heads)
        raise RuntimeError(
            "Multiple Alembic heads detected: "
            f"{formatted}. Apply the merge revision 20251212100000 or run "
            "`alembic merge` to unify branches before bootstrapping."
        )

    return resolved_heads


# --------------------------------------------------------------------
# Main init_db entrypoint
# --------------------------------------------------------------------


def init_db() -> None:
    """Bootstrap a fresh/local DB so the app can import without errors."""

    try:
        _assert_single_migration_head()
    except RuntimeError as exc:
        # Provide a clear, single-line hint so container orchestrators surface
        # the actionable cause instead of reboot-looping on an opaque stack
        # trace. The error is still raised so CI/CD fails fast.
        print(f"Migration head check failed: {exc}")
        raise

    # 1) Always try Alembic migrations first; if they fail, hard reset.
    try:
        safe_run(["alembic", "upgrade", "head"], check=True)
        print("Alembic upgrade: OK")
    except FileNotFoundError:
        print("Alembic upgrade skipped or not available (FileNotFoundError).")
    except subprocess.CalledProcessError:
        print("Alembic upgrade failed; resetting schema and retrying...")
        _reset_schema()
        safe_run(["alembic", "upgrade", "head"], check=True)
        print("Alembic upgrade after reset: OK")

    engine = get_engine()

    # 2) For SQLite dev runs this can create missing region/city tables;
    #    for Postgres it’s effectively a no-op thanks to Alembic.
    metadata.create_all(engine)

    # 3) Seed reference data + demo accounts (if enabled)
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
                conn.execute(
                    cities.insert().values(
                        region_id=region_id,
                        name=city_name,
                    )
                )

        seed_demo = os.environ.get("SEED_DEMO_DATA") == "1" and os.environ.get(
            "FLASK_ENV", "development"
        ) != "production"

        if seed_demo:
            # ----------------------------------------------------------------
            # Core admin account
            # ----------------------------------------------------------------
            admin_username = os.environ.get("ADMIN_USERNAME", "admin")
            admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
            password_hash = hash_password(admin_password)
            admin_secret = pyotp.random_base32()

            _insert_ignore(
                conn,
                users,
                dict(
                    username=admin_username,
                    email=f"{admin_username}@berhanpharma.com",
                    password_hash=password_hash,
                    # NOTE: mfa_secret may or may not be a users column. If the
                    # column doesn't exist, _insert_ignore will drop this key.
                    mfa_secret=admin_secret,
                    permissions=(
                        "add_report,view_orders,user_management,add_inventory,"
                        "receive_inventory,inventory_out,inventory_report,add_tender,"
                        "tenders_list,tenders_report,put_order,maintenance_request,"
                        "maintenance_status,maintenance_followup,maintenance_report"
                    ),
                    approved_by_ceo=True,
                    role="Admin",
                    last_password_change=datetime.now(),
                    is_active=True,  # only applied if column exists
                ),
            )
            print(
                f"Seeded admin {admin_username}@berhanpharma.com "
                f"with MFA secret: {admin_secret}"
            )

            # ----------------------------------------------------------------
            # Extra admin accounts by phone
            # ----------------------------------------------------------------
            for phone in admin_phones:
                password_hash = hash_password(phone)
                secret = pyotp.random_base32()
                _insert_ignore(
                    conn,
                    users,
                    dict(
                        username=phone,
                        email=f"{phone}@berhanpharma.com",
                        password_hash=password_hash,
                        mfa_secret=secret,
                        permissions=(
                            "add_report,view_orders,user_management,add_inventory,"
                            "receive_inventory,inventory_out,inventory_report,add_tender,"
                            "tenders_list,tenders_report,put_order,maintenance_request,"
                            "maintenance_status,maintenance_followup,maintenance_report"
                        ),
                        approved_by_ceo=True,
                        role="Admin",
                        last_password_change=datetime.now(),
                        is_active=True,
                    ),
                )
                print(
                    f"Seeded admin {phone}@berhanpharma.com "
                    f"with MFA secret: {secret}"
                )

            # ----------------------------------------------------------------
            # Sales reps (demo)
            # ----------------------------------------------------------------
            for phone in employee_phones:
                password_hash = hash_password(phone)
                secret = pyotp.random_base32()
                _insert_ignore(
                    conn,
                    users,
                    dict(
                        username=phone,
                        email=f"{phone}@berhanpharma.com",
                        password_hash=password_hash,
                        mfa_secret=secret,
                        permissions="add_report,put_order,view_orders",
                        approved_by_ceo=True,
                        role="Sales Rep",
                        last_password_change=datetime.now(),
                        is_active=True,
                    ),
                )
        elif seed_demo:
            # This branch is unreachable with the current condition, but kept
            # for clarity of intent: we never seed demo data in production.
            print("SEED_DEMO_DATA ignored in production environment")

        # ----------------------------------------------------------------
        # Ensure org_id + RLS on key multi-tenant tables, if they exist.
        # ----------------------------------------------------------------
        for table_name in ("orders", "tenders", "inventory", "audit_logs"):
            if _table_exists(conn, table_name):
                conn.execute(
                    text(
                        f'ALTER TABLE "{table_name}" '
                        'ADD COLUMN IF NOT EXISTS org_id INTEGER '
                        'REFERENCES organizations(id)'
                    )
                )
                conn.execute(
                    text(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY')
                )
                conn.execute(
                    text(f'DROP POLICY IF EXISTS org_rls ON "{table_name}"')
                )
                conn.execute(
                    text(
                        f'CREATE POLICY org_rls ON "{table_name}" '
                        "USING (org_id = current_setting('erp.org_id')::INTEGER) "
                        "WITH CHECK (org_id = current_setting('erp.org_id')::INTEGER)"
                    )
                )

    print("Database initialized / schema ensured successfully.")


# --------------------------------------------------------------------
# Helper hashing API (stable across backends) – external callers
# --------------------------------------------------------------------


def verify_password(pw: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    try:
        return ph.verify(hashed, pw)
    except Exception:
        return False


if __name__ == "__main__":  # pragma: no cover
    init_db()
