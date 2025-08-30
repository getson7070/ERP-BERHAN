import os
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app  # noqa: E402
from db import get_db  # noqa: E402


@pytest.fixture
def app():
    return create_app()


def test_foreign_keys_enforced(app):
    with app.app_context():
        conn = get_db()
        # Enable FK enforcement for SQLite
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("DROP TABLE IF EXISTS child"))
        conn.execute(text("DROP TABLE IF EXISTS parent"))
        conn.execute(text("CREATE TABLE parent(id INTEGER PRIMARY KEY)"))
        conn.execute(
            text(
                "CREATE TABLE child(id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))"
            )
        )
        with pytest.raises((IntegrityError, sqlite3.IntegrityError)):
            conn.execute(text("INSERT INTO child (parent_id) VALUES (999)"))
        conn.rollback()
        conn.close()
