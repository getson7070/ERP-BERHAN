import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app
from db import get_db


def test_row_level_isolation(tmp_path, monkeypatch):
    db_file = tmp_path / "rls.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO inventory_items (org_id, name, sku, quantity) VALUES (1,'A','A1',1),(2,'B','B2',1)"
        )
        cur.execute(
            "CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, description TEXT)"
        )
        cur.execute(
            "INSERT INTO orders (org_id, description) VALUES (1,'O1'),(2,'O2')"
        )
        cur.execute(
            "CREATE TABLE tenders (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, description TEXT, workflow_state TEXT)"
        )
        cur.execute(
            "INSERT INTO tenders (org_id, description, workflow_state) VALUES (1,'T1','open'),(2,'T2','open')"
        )
        cur.execute(
            "CREATE TABLE audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, org_id INTEGER, action TEXT, created_at TIMESTAMP)"
        )
        cur.execute(
            "INSERT INTO audit_logs (org_id, action, created_at) VALUES (1,'A1','2020-01-01'),(2,'A2','2020-01-01')"
        )
        conn.commit()
        cur.close()
        conn.close()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["org_id"] = 1
    rv = client.get("/inventory/")
    assert b"B" not in rv.data

    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        # Skip direct RLS checks when using SQLite which lacks enforcement
        if conn._dialect.name == "sqlite":
            pytest.skip("RLS enforcement requires PostgreSQL")
        cur.execute("SELECT description FROM orders")
        assert all(row[0] != 'O2' for row in cur.fetchall())
        with pytest.raises(Exception):
            cur.execute("INSERT INTO orders (org_id, description) VALUES (2,'X')")
        cur.close()
        conn.rollback()
        conn.close()
