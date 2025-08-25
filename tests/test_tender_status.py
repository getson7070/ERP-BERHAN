import os
from datetime import date
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def _prepare_app(tmp_path):
    """Create a test app bound to a temporary SQLite database."""
    db_path = tmp_path / "test.db"
    if db_path.exists():
        db_path.unlink()
    # Configure SQLAlchemy to use this sqlite database
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["TEST_DB_PATH"] = str(db_path)
    import importlib, db, erp
    importlib.reload(db)
    erp.get_db = db.get_db  # refresh DB engine without reloading metrics
    from erp import create_app  # import after updating get_db reference
    app = create_app()
    app.config["TESTING"] = True
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        DROP TABLE IF EXISTS access_logs;
        DROP TABLE IF EXISTS role_assignments;
        DROP TABLE IF EXISTS role_permissions;
        DROP TABLE IF EXISTS permissions;
        DROP TABLE IF EXISTS roles;
        DROP TABLE IF EXISTS organizations;
        DROP TABLE IF EXISTS tenders;
        DROP TABLE IF EXISTS tender_types;
        CREATE TABLE organizations (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE permissions (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE role_permissions (role_id INTEGER, permission_id INTEGER);
        CREATE TABLE role_assignments (user_id INTEGER, org_id INTEGER, role_id INTEGER);
        CREATE TABLE tender_types (id INTEGER PRIMARY KEY, type_name TEXT);
        CREATE TABLE tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tender_type_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            due_date DATE NOT NULL,
            status TEXT,
            workflow_state TEXT,
            result TEXT,
            awarded_to TEXT,
            award_date DATE,
            username TEXT,
            institution TEXT,
            envelope_type TEXT,
            private_key TEXT,
            tech_key TEXT,
            fin_key TEXT
        );
        CREATE TABLE access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT, ip TEXT, device TEXT, timestamp DATETIME
        );
        INSERT INTO organizations (id, name) VALUES (1, 'Org');
        INSERT INTO roles (id, name) VALUES (1, 'Admin');
        INSERT INTO permissions (id, name) VALUES (1, 'tenders_list');
        INSERT INTO role_permissions (role_id, permission_id) VALUES (1,1);
        INSERT INTO role_assignments (user_id, org_id, role_id) VALUES (1,1,1);
        """
    )
    conn.commit()
    conn.close()
    return app


def _login(client):
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['role'] = 'Admin'
        sess['user_id'] = 1
        sess['org_id'] = 1
        # Bypass DB permission check for sqlite tests
        sess['permissions'] = ['tenders_list']


def test_evaluate_marks_evaluated(tmp_path):
    app = _prepare_app(tmp_path)
    conn = sqlite3.connect(os.environ['TEST_DB_PATH'])
    conn.execute("INSERT INTO tender_types (type_name) VALUES ('Test')")
    conn.execute("INSERT INTO tenders (tender_type_id, description, due_date, workflow_state, username, envelope_type) VALUES (1,'desc',?, 'opening_minute','u','One Envelope')", (date.today(),))
    conn.commit()
    conn.close()
    client = app.test_client()
    _login(client)
    client.post('/tenders/1/advance', data={'evaluation_complete': '1'})
    conn = sqlite3.connect(os.environ['TEST_DB_PATH'])
    conn.row_factory = sqlite3.Row
    state = conn.execute('SELECT workflow_state FROM tenders WHERE id=1').fetchone()['workflow_state']
    conn.close()
    assert state == 'evaluated'


def test_award_marks_awarded(tmp_path):
    app = _prepare_app(tmp_path)
    conn = sqlite3.connect(os.environ['TEST_DB_PATH'])
    conn.execute("INSERT INTO tender_types (type_name) VALUES ('Test')")
    conn.execute("INSERT INTO tenders (tender_type_id, description, due_date, workflow_state, username, envelope_type) VALUES (1,'desc',?, 'evaluated','u','One Envelope')", (date.today(),))
    conn.commit()
    conn.close()
    client = app.test_client()
    _login(client)
    client.post('/tenders/1/advance', data={'result': 'won', 'awarded_to': 'Supplier', 'award_date': '2024-01-01'})
    conn = sqlite3.connect(os.environ['TEST_DB_PATH'])
    conn.row_factory = sqlite3.Row
    row = conn.execute('SELECT workflow_state, awarded_to FROM tenders WHERE id=1').fetchone()
    conn.close()
    assert row['workflow_state'] == 'awarded'
    assert row['awarded_to'] == 'Supplier'
