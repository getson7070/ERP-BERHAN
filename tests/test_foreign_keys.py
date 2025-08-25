import os
import sqlite3
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import get_db


def test_foreign_keys_enforced():
    conn = get_db()
    fk = conn.execute('PRAGMA foreign_keys').fetchone()[0]
    assert fk == 1
    conn.execute('CREATE TABLE parent(id INTEGER PRIMARY KEY)')
    conn.execute('CREATE TABLE child(id INTEGER PRIMARY KEY, parent_id INTEGER, FOREIGN KEY(parent_id) REFERENCES parent(id))')
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute('INSERT INTO child (parent_id) VALUES (1)')
    conn.close()
