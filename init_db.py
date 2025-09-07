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
    cur.execute("SELECT 1 FROM roles WHERE name=%s", (name,))
    return cur.fetchone() is not None


def _org_id_for(cur, org_name: str) -> int | None:
    cur.execute("SELECT id FROM organizations WHERE name=%s", (org_name,))
    row = cur.fetchone()
    return row[0] if row else None


def init_db():
    """Bootstrap a fresh/local DB so the app can import without errors."""

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

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS organizations (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS roles (
            id SERIAL PRIMARY KEY,
            org_id INTEGER REFERENCES organizations(id),
            name TEXT NOT NULL,
            description TEXT
        )
        """
    )
    cursor.execute("ALTER TABLE roles ADD COLUMN IF NOT EXISTS description TEXT")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS permissions (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER REFERENCES roles(id),
            permission_id INTEGER REFERENCES permissions(id),
            PRIMARY KEY (role_id, permission_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_type TEXT NOT NULL CHECK(user_type IN ('employee', 'client')),
            tin TEXT,
            username TEXT UNIQUE,
            institution_name TEXT,
            address TEXT,
            phone TEXT,
            region TEXT,
            city TEXT,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            mfa_secret TEXT,
            permissions TEXT,
            approved_by_ceo BOOLEAN DEFAULT FALSE,
            last_login TIMESTAMP,
            hire_date DATE,
            salary REAL,
            role TEXT,
            failed_attempts INTEGER DEFAULT 0,
            account_locked BOOLEAN DEFAULT FALSE,
            last_password_change TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS role_assignments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            role_id INTEGER REFERENCES roles(id),
            org_id INTEGER REFERENCES organizations(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS access_logs (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            ip TEXT NOT NULL,
            device TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            org_id INTEGER REFERENCES organizations(id),
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS password_resets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            tin TEXT,
            message TEXT NOT NULL,
            date TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'pending'
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS regions_cities (
            id SERIAL PRIMARY KEY,
            region TEXT NOT NULL,
            city TEXT NOT NULL
        )
        """
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

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            institution TEXT NOT NULL,
            location TEXT NOT NULL,
            owner TEXT,
            phone TEXT NOT NULL,
            visit_date DATE NOT NULL,
            interested_products TEXT NOT NULL,
            outcome TEXT NOT NULL,
            sale_amount REAL,
            visit_type TEXT NOT NULL,
            follow_up_details TEXT,
            sales_rep TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY,
            item_code TEXT NOT NULL,
            description TEXT NOT NULL,
            pack_size TEXT NOT NULL,
            brand TEXT NOT NULL,
            type TEXT NOT NULL,
            exp_date DATE,
            category TEXT NOT NULL,
            stock INTEGER DEFAULT 0
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            item_id INTEGER NOT NULL REFERENCES inventory(id),
            quantity INTEGER NOT NULL,
            customer TEXT NOT NULL,
            sales_rep TEXT NOT NULL,
            vat_exempt BOOLEAN DEFAULT FALSE,
            status TEXT DEFAULT 'pending',
            delivery_status TEXT DEFAULT 'pending'
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS maintenance (
            id SERIAL PRIMARY KEY,
            equipment_id INTEGER NOT NULL,
            request_date TIMESTAMP NOT NULL,
            type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            report TEXT,
            username TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        "ALTER TABLE maintenance ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending'"
    )
    cursor.execute("ALTER TABLE maintenance ADD COLUMN IF NOT EXISTS report TEXT")
    cursor.execute("ALTER TABLE maintenance ADD COLUMN IF NOT EXISTS username TEXT")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_types (
            id SERIAL PRIMARY KEY,
            type_name TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tenders (
            id SERIAL PRIMARY KEY,
            tender_type_id INTEGER NOT NULL REFERENCES tender_types(id),
            description TEXT NOT NULL,
            due_date DATE NOT NULL,
            status TEXT DEFAULT 'Open',
            workflow_state TEXT NOT NULL DEFAULT 'advert_registered',
            result TEXT,
            awarded_to TEXT,
            award_date DATE,
            username TEXT NOT NULL,
            institution TEXT,
            envelope_type TEXT NOT NULL,
            private_key TEXT,
            tech_key TEXT,
            fin_key TEXT
        )
        """
    )

    cursor.execute(
        "ALTER TABLE tenders ADD COLUMN IF NOT EXISTS workflow_state TEXT NOT NULL DEFAULT 'advert_registered'"
    )
    cursor.execute(
        "UPDATE tenders SET workflow_state='advert_registered' WHERE workflow_state='advertised'"
    )
    cursor.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS result TEXT")
    cursor.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS awarded_to TEXT")
    cursor.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS award_date DATE")

    for ttype in ("EGP Portal", "Paper Tender", "NGO/UN Portal Tender"):
        cursor.execute(
            "INSERT INTO tender_types (type_name) VALUES (%s) ON CONFLICT DO NOTHING",
            (ttype,),
        )

    default_org_name = os.environ.get("DEFAULT_ORG_NAME", "Default Org")
    cursor.execute(
        "INSERT INTO organizations (name) VALUES (%s) ON CONFLICT DO NOTHING",
        (default_org_name,),
    )
    org_id = _org_id_for(cursor, default_org_name)

    if not _role_exists(cursor, "Admin"):
        cursor.execute(
            "INSERT INTO roles (org_id, name, description) VALUES (%s, %s, %s)",
            (org_id, "Admin", "Full platform access"),
        )

    seed_demo = os.environ.get("SEED_DEMO_DATA") == "1"
    if seed_demo and os.environ.get("ENV") != "production":
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

    try:
        subprocess.run(["alembic", "stamp", "head"], check=True)
        print("Alembic stamp: OK")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Alembic stamp skipped or failed.")

    print("Database initialized / schema ensured successfully.")


if __name__ == "__main__":
    init_db()
