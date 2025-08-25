import os
import sqlite3
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app
from db import get_db


@pytest.fixture
def app():
    return create_app()


def test_foreign_keys_enforced(app):
    with app.app_context():
        conn = get_db()
        fk = conn.execute('PRAGMA foreign_keys').fetchone()[0]
        assert fk == 1
        conn.execute('DROP TABLE IF EXISTS child')
        conn.execute('DROP TABLE IF EXISTS parent')
        conn.execute('CREATE TABLE parent(id INTEGER PRIMARY KEY)')
        conn.execute('CREATE TABLE child(id INTEGER PRIMARY KEY, parent_id INTEGER, FOREIGN KEY(parent_id) REFERENCES parent(id))')
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute('INSERT INTO child (parent_id) VALUES (1)')
        conn.close()

