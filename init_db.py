import subprocess
from datetime import datetime
from argon2 import PasswordHasher
import os
from db import get_db
from psycopg2 import sql


ph = PasswordHasher(
    time_cost=int(os.environ.get("ARGON2_TIME_COST", "3")),
    memory_cost=int(os.environ.get("ARGON2_MEMORY_COST", "65536")),
    parallelism=int(os.environ.get("ARGON2_PARALLELISM", "2")),
)


def hash_password(password: str) -> str:
    return ph.hash(password)


def init_db():
    # Apply database migrations to ensure the latest schema
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(
            "Alembic migration skipped or failed; ensure alembic is installed and configured."
        )

    conn = get_db()
    cursor = conn.cursor()

    app_user = os.environ.get("APP_DB_USER")
    app_password = os.environ.get("APP_DB_PASSWORD")
    if app_user and app_password:
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname=%s",
            (app_user,),
        )
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
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}"
            ).format(sql.Identifier(app_user))
        )

    # Create users table
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

    # RBAC tables
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
    # Older deployments may already have a ``roles`` table without the
    # ``description`` column.  Attempt to add it and ignore errors if it
    # already exists, ensuring the schema is consistent across environments.
    try:
        cursor.execute("ALTER TABLE roles ADD COLUMN IF NOT EXISTS description TEXT")
    except Exception:
        pass
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
    CREATE TABLE IF NOT EXISTS role_assignments (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        role_id INTEGER REFERENCES roles(id),
        org_id INTEGER REFERENCES organizations(id)
    )
    """
    )

    # Create access_logs table for IP/device logging
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

    # Password reset requests
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

    # Create other tables
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
        ("Southern Nations, Nationalities, and Peoples Region", "Arba Minch"),
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
    CREATE TABLE IF NOT EXISTS inventory_movements (
        id SERIAL PRIMARY KEY,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        action TEXT NOT NULL,
        sub_action TEXT,
        date TIMESTAMP NOT NULL,
        username TEXT NOT NULL,
        order_id INTEGER,
        FOREIGN KEY (item_id) REFERENCES inventory(id),
        FOREIGN KEY (order_id) REFERENCES orders(id)
    )
    """
    )

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
        tender_type_id INTEGER NOT NULL,
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
        fin_key TEXT,
        FOREIGN KEY (tender_type_id) REFERENCES tender_types(id)
    )
    """
    )

    cursor.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name='tenders'"
    )
    existing = [row[0] for row in cursor.fetchall()]
    if "workflow_state" not in existing:
        cursor.execute(
            "ALTER TABLE tenders ADD COLUMN workflow_state TEXT NOT NULL DEFAULT 'advert_registered'"
        )
    else:
        cursor.execute(
            "UPDATE tenders SET workflow_state='advert_registered' WHERE workflow_state='advertised'"
        )
    if "result" not in existing:
        cursor.execute("ALTER TABLE tenders ADD COLUMN result TEXT")
    if "awarded_to" not in existing:
        cursor.execute("ALTER TABLE tenders ADD COLUMN awarded_to TEXT")
    if "award_date" not in existing:
        cursor.execute("ALTER TABLE tenders ADD COLUMN award_date DATE")

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        customer TEXT NOT NULL,
        sales_rep TEXT NOT NULL,
        vat_exempt BOOLEAN DEFAULT FALSE,
        status TEXT DEFAULT 'pending',
        delivery_status TEXT DEFAULT 'pending',
        FOREIGN KEY (item_id) REFERENCES inventory(id)
    )
    """
    )

    cursor.execute("DROP TABLE IF EXISTS maintenance")
    cursor.execute(
        """
    CREATE TABLE maintenance (
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
        "INSERT INTO tender_types (type_name) VALUES (%s) ON CONFLICT DO NOTHING",
        ("EGP Portal",),
    )
    cursor.execute(
        "INSERT INTO tender_types (type_name) VALUES (%s) ON CONFLICT DO NOTHING",
        ("Paper Tender",),
    )
    cursor.execute(
        "INSERT INTO tender_types (type_name) VALUES (%s) ON CONFLICT DO NOTHING",
        ("NGO/UN Portal Tender",),
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
            "INSERT INTO users (user_type, username, password_hash, mfa_secret, permissions, approved_by_ceo, role, last_password_change) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
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
                "INSERT INTO users (user_type, username, password_hash, mfa_secret, permissions, approved_by_ceo, role, last_password_change) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
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
                "INSERT INTO users (user_type, username, password_hash, mfa_secret, permissions, approved_by_ceo, role, last_password_change) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
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
                "CREATE POLICY org_rls ON {} USING (org_id = current_setting('erp.org_id')::INTEGER) WITH CHECK (org_id = current_setting('erp.org_id')::INTEGER)"
            ).format(sql.Identifier(table))
        )

    conn.commit()
    conn.close()
    print("Database initialized or schema updated successfully.")


if __name__ == "__main__":
    init_db()
