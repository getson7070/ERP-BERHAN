import subprocess
import subprocess
from datetime import datetime
import os

from argon2 import PasswordHasher
from psycopg2 import sql

from db import get_db


ph = PasswordHasher(
    time_cost=int(os.environ.get("ARGON2_TIME_COST", "3")),
    memory_cost=int(os.environ.get("ARGON2_MEMORY_COST", "65536")),
    parallelism=int(os.environ.get("ARGON2_PARALLELISM", "2")),
)


def hash_password(password: str) -> str:
    return ph.hash(password)


def _role_exists(cur, name: str) -> bool:
    if not _table_exists(cur, "roles"):
        return False
    cur.execute("SELECT 1 FROM roles WHERE name=%s", (name,))
    return cur.fetchone() is not None


def _org_id_for(cur, org_name: str) -> int | None:
    if not _table_exists(cur, "organizations"):
        return None
    cur.execute("SELECT id FROM organizations WHERE name=%s", (org_name,))
    row = cur.fetchone()
    return row[0] if row else None


def _table_exists(cur, table: str) -> bool:
    cur.execute("SELECT to_regclass(%s)", (f"public.{table}",))
    return cur.fetchone()[0] is not None


def _reset_schema() -> None:
    """Drop and recreate the public schema to clear stray tables."""
    conn = get_db()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
    cur.execute("CREATE SCHEMA public")
    cur.close()
    conn.close()


def init_db():
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

    conn = get_db()
    cursor = conn.cursor()

    app_user = os.environ.get("APP_DB_USER")
    app_password = os.environ.get("APP_DB_PASSWORD")
    if app_user and app_password:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (app_user,))
        if cursor.fetchone() is None:
            cursor.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(
                    sql.Identifier(app_user)
                ),
                (app_password,),
            )
        cursor.execute("SELECT current_database()")
        dbname = cursor.fetchone()[0]
        cursor.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(dbname), sql.Identifier(app_user)
            )
        )
        cursor.execute(
            sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(
                sql.Identifier(app_user)
            )
        )
        cursor.execute(
            sql.SQL(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}"
            ).format(sql.Identifier(app_user))
        )
        cursor.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}"
            ).format(sql.Identifier(app_user))
        )

    if _table_exists(cursor, "tender_types"):
        for ttype in ("EGP Portal", "Paper Tender", "NGO/UN Portal Tender"):
            cursor.execute(
                "INSERT INTO tender_types (type_name) VALUES (%s) ON CONFLICT DO NOTHING",
                (ttype,),
            )

    org_id = None
    if _table_exists(cursor, "organizations"):
        default_org_name = os.environ.get("DEFAULT_ORG_NAME", "Default Org")
        cursor.execute(
            "INSERT INTO organizations (name) VALUES (%s) ON CONFLICT DO NOTHING",
            (default_org_name,),
        )
        org_id = _org_id_for(cursor, default_org_name)

    if org_id and _table_exists(cursor, "roles") and not _role_exists(cursor, "Admin"):
        cursor.execute(
            "INSERT INTO roles (org_id, name, description) VALUES (%s, %s, %s)",
            (org_id, "Admin", "Full platform access"),
        )

    if _table_exists(cursor, "regions_cities"):
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
            (
                "Southern Nations, Nationalities, and Peoples Region",
                "Arba Minch",
            ),
            ("Tigray", "Mekelle"),
            ("Addis Ababa", "Addis Ababa"),
            ("Dire Dawa", "Dire Dawa"),
        ]
        cursor.executemany(
            "INSERT INTO regions_cities (region, city) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            regions_cities_data,
        )

    seed_demo = os.environ.get("SEED_DEMO_DATA") == "1"
    if seed_demo and os.environ.get("ENV") != "production" and _table_exists(cursor, "users"):
        admin_username = os.environ.get("ADMIN_USERNAME")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if not admin_username or not admin_password:
            raise RuntimeError(
                "ADMIN_USERNAME and ADMIN_PASSWORD required when SEED_DEMO_DATA=1"
            )

        password_hash = hash_password(admin_password)
        cursor.execute(
            """
            INSERT INTO users (
                user_type, username, password_hash, mfa_secret, permissions,
                approved_by_ceo, role, last_password_change
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                "employee",
                admin_username,
                password_hash,
                "JBSWY3DPEHPK3PXP",
                "add_report,view_orders,user_management,add_inventory,receive_inventory,inventory_out,inventory_report,add_tender,tenders_list,tenders_report,put_order,maintenance_request,maintenance_status,maintenance_followup,maintenance_report",
                True,
                "Admin",
                datetime.now(),
            ),
        )

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
            cursor.execute(
                """
                INSERT INTO users (
                    user_type, username, password_hash, mfa_secret, permissions,
                    approved_by_ceo, role, last_password_change
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    "employee",
                    phone,
                    password_hash,
                    "JBSWY3DPEHPK3PXP",
                    "add_report,view_orders,user_management,add_inventory,receive_inventory,inventory_out,inventory_report,add_tender,tenders_list,tenders_report,put_order,maintenance_request,maintenance_status,maintenance_followup,maintenance_report",
                    True,
                    "Admin",
                    datetime.now(),
                ),
            )
        for phone in employee_phones:
            password_hash = hash_password(phone)
            cursor.execute(
                """
                INSERT INTO users (
                    user_type, username, password_hash, mfa_secret, permissions,
                    approved_by_ceo, role, last_password_change
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    "employee",
                    phone,
                    password_hash,
                    "JBSWY3DPEHPK3PXP",
                    "add_report,put_order,view_orders",
                    True,
                    "Sales Rep",
                    datetime.now(),
                ),
            )
    elif seed_demo:
        print("SEED_DEMO_DATA ignored in production environment")

    for table in ("orders", "tenders", "inventory", "audit_logs"):
        if _table_exists(cursor, table):
            cursor.execute(
                sql.SQL(
                    "ALTER TABLE {} ADD COLUMN IF NOT EXISTS org_id INTEGER REFERENCES organizations(id)"
                ).format(sql.Identifier(table))
            )
            cursor.execute(
                sql.SQL("ALTER TABLE {} ENABLE ROW LEVEL SECURITY").format(
                    sql.Identifier(table)
                )
            )
            cursor.execute(
                sql.SQL("DROP POLICY IF EXISTS org_rls ON {}").format(sql.Identifier(table))
            )
            cursor.execute(
                sql.SQL(
                    "CREATE POLICY org_rls ON {} "
                    "USING (org_id = current_setting('erp.org_id')::INTEGER) "
                    "WITH CHECK (org_id = current_setting('erp.org_id')::INTEGER)"
                ).format(sql.Identifier(table))
            )

    conn.commit()
    cursor.close()
    conn.close()

    print("Database initialized / schema ensured successfully.")


if __name__ == "__main__":
    init_db()
