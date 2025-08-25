import os
from datetime import date
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from erp import create_app


def _prepare_app(tmp_path):
    db_path = tmp_path / 'test.db'
    if db_path.exists():
        db_path.unlink()
    os.environ['DATABASE_PATH'] = str(db_path)
    import db
    db.DATABASE_PATH = str(db_path)
    app = create_app()
    app.config['TESTING'] = True
    conn = sqlite3.connect(os.environ['DATABASE_PATH'])
    conn.executescript(
        """
        DROP TABLE IF EXISTS access_logs;
        DROP TABLE IF EXISTS tenders;
        DROP TABLE IF EXISTS tender_types;
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
            user TEXT,
            institution TEXT,
            envelope_type TEXT,
            private_key TEXT,
            tech_key TEXT,
            fin_key TEXT
        );
        CREATE TABLE access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT, ip TEXT, device TEXT, timestamp DATETIME
        );
        """
    )
    conn.commit()
    conn.close()
    return app


def _login(client):
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['role'] = 'Admin'
        sess['permissions'] = ['tenders_list']


def test_evaluate_marks_evaluated(tmp_path):
    app = _prepare_app(tmp_path)
    conn = sqlite3.connect(os.environ['DATABASE_PATH'])
    conn.execute("INSERT INTO tender_types (type_name) VALUES ('Test')")
    conn.execute("INSERT INTO tenders (tender_type_id, description, due_date, workflow_state, user, envelope_type) VALUES (1,'desc',?, 'opening_minute','u','One Envelope')", (date.today(),))
    conn.commit()
    conn.close()
    client = app.test_client()
    _login(client)
    client.post('/tenders/1/advance', data={'evaluation_complete': '1'})
    conn = sqlite3.connect(os.environ['DATABASE_PATH'])
    conn.row_factory = sqlite3.Row
    state = conn.execute('SELECT workflow_state FROM tenders WHERE id=1').fetchone()['workflow_state']
    conn.close()
    assert state == 'evaluated'


def test_award_marks_awarded(tmp_path):
    app = _prepare_app(tmp_path)
    conn = sqlite3.connect(os.environ['DATABASE_PATH'])
    conn.execute("INSERT INTO tender_types (type_name) VALUES ('Test')")
    conn.execute("INSERT INTO tenders (tender_type_id, description, due_date, workflow_state, user, envelope_type) VALUES (1,'desc',?, 'evaluated','u','One Envelope')", (date.today(),))
    conn.commit()
    conn.close()
    client = app.test_client()
    _login(client)
    client.post('/tenders/1/advance', data={'result': 'won', 'awarded_to': 'Supplier', 'award_date': '2024-01-01'})
    conn = sqlite3.connect(os.environ['DATABASE_PATH'])
    conn.row_factory = sqlite3.Row
    row = conn.execute('SELECT workflow_state, awarded_to FROM tenders WHERE id=1').fetchone()
    conn.close()
    assert row['workflow_state'] == 'awarded'
    assert row['awarded_to'] == 'Supplier'
