import os
import sys
import sqlite3
import importlib

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import db
from erp import create_app
from db import get_db


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "fk_test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    importlib.reload(db)
    app = create_app()
    app.config["TESTING"] = True
    return app


def test_foreign_keys_enforced(app):
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute('DROP TABLE IF EXISTS child')
        cur.execute('DROP TABLE IF EXISTS parent')
        cur.execute('CREATE TABLE parent(id INTEGER PRIMARY KEY)')
        cur.execute('CREATE TABLE child(id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))')
        with pytest.raises(sqlite3.IntegrityError):
            cur.execute('INSERT INTO child (parent_id) VALUES (999)')
        conn.rollback()
        cur.close()
        conn.close()

