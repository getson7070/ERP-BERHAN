import sqlite3
from argon2 import PasswordHasher


ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)

def init_db():
    conn = sqlite3.connect('erp.db')
    cursor = conn.cursor()

    # Drop existing tables to ensure clean schema
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS access_logs")
    conn.commit()

    # Create users table
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        permissions TEXT,
        approved_by_ceo BOOLEAN DEFAULT FALSE,
        last_login DATETIME,
        hire_date DATE,
        salary REAL,
        role TEXT
    )
    ''')

    # Create access_logs table for IP/device logging
    cursor.execute('''
    CREATE TABLE access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        ip TEXT NOT NULL,
        device TEXT NOT NULL,
        timestamp DATETIME NOT NULL
    )
    ''')

    # Create other tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tin TEXT,
        message TEXT NOT NULL,
        date DATETIME NOT NULL,
        status TEXT DEFAULT 'pending'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS regions_cities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region TEXT NOT NULL,
        city TEXT NOT NULL
    )
    ''')

    regions_cities_data = [
        ('Amhara', 'Bahir Dar'), ('Amhara', 'Gondar'), ('Afar', 'Semera'), ('Benishangul-Gumuz', 'Asosa'),
        ('Gambela', 'Gambela'), ('Harari', 'Harar'), ('Oromia', 'Adama'), ('Oromia', 'Jimma'),
        ('Sidama', 'Hawassa'), ('Somali', 'Jijiga'), ('South West Ethiopia Peoples Region', 'Bonga'),
        ('Southern Nations, Nationalities, and Peoples Region', 'Arba Minch'), ('Tigray', 'Mekelle'),
        ('Addis Ababa', 'Addis Ababa'), ('Dire Dawa', 'Dire Dawa'),
    ]
    cursor.executemany('INSERT OR IGNORE INTO regions_cities (region, city) VALUES (?, ?)', regions_cities_data)

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT NOT NULL,
        description TEXT NOT NULL,
        pack_size TEXT NOT NULL,
        brand TEXT NOT NULL,
        type TEXT NOT NULL,
        exp_date DATE,
        category TEXT NOT NULL,
        stock INTEGER DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        action TEXT NOT NULL,
        sub_action TEXT,
        date DATETIME NOT NULL,
        user TEXT NOT NULL,
        order_id INTEGER,
        FOREIGN KEY (item_id) REFERENCES inventory(id),
        FOREIGN KEY (order_id) REFERENCES orders(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tender_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tenders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tender_type_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        due_date DATE NOT NULL,
        status TEXT DEFAULT 'Open',
        user TEXT NOT NULL,
        institution TEXT,
        envelope_type TEXT NOT NULL,
        private_key TEXT,
        tech_key TEXT,
        fin_key TEXT,
        FOREIGN KEY (tender_type_id) REFERENCES tender_types(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        customer TEXT NOT NULL,
        sales_rep TEXT NOT NULL,
        vat_exempt BOOLEAN DEFAULT FALSE,
        status TEXT DEFAULT 'pending',
        delivery_status TEXT DEFAULT 'pending',
        FOREIGN KEY (item_id) REFERENCES inventory(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        request_date DATETIME NOT NULL,
        type TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        report TEXT,
        user TEXT NOT NULL,
        FOREIGN KEY (user) REFERENCES users(tin)
    )
    ''')

    cursor.execute('INSERT OR IGNORE INTO tender_types (type_name) VALUES (?)', ('EGP Portal',))
    cursor.execute('INSERT OR IGNORE INTO tender_types (type_name) VALUES (?)', ('Paper Tender',))
    cursor.execute('INSERT OR IGNORE INTO tender_types (type_name) VALUES (?)', ('NGO/UN Portal Tender',))

    cursor.execute('DELETE FROM users WHERE username = "admin"')
    password_hash = hash_password('admin123')
    cursor.execute('INSERT INTO users (user_type, username, password_hash, permissions, approved_by_ceo, role) VALUES (?, ?, ?, ?, ?, ?)',
                   ('employee', 'admin', password_hash, 'add_report,view_orders,user_management,add_inventory,receive_inventory,inventory_out,inventory_report,add_tender,tenders_list,tenders_report,put_order,maintenance_request,maintenance_status,maintenance_followup,maintenance_report', True, 'Admin'))

    admin_phones = ['0946423021', '0984707070', '0969111144']
    employee_phones = ['0969351111', '0969361111', '0969371111', '0969381111', '0969161111', '0923804931', '0911183488']
    for phone in admin_phones:
        password_hash = hash_password(phone)
        cursor.execute('INSERT INTO users (user_type, username, password_hash, permissions, approved_by_ceo, role) VALUES (?, ?, ?, ?, ?, ?)',
                       ('employee', phone, password_hash, 'add_report,view_orders,user_management,add_inventory,receive_inventory,inventory_out,inventory_report,add_tender,tenders_list,tenders_report,put_order,maintenance_request,maintenance_status,maintenance_followup,maintenance_report', True, 'Admin'))
    for phone in employee_phones:
        password_hash = hash_password(phone)
        cursor.execute('INSERT INTO users (user_type, username, password_hash, permissions, approved_by_ceo, role) VALUES (?, ?, ?, ?, ?, ?)',
                       ('employee', phone, password_hash, 'add_report,put_order,view_orders', True, 'Sales Rep'))

    conn.commit()
    conn.close()
    print("Database initialized or schema updated successfully.")

if __name__ == '__main__':
    init_db()
