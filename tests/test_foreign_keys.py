import os
import sys

import pytest
import psycopg2
from psycopg2 import errors

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app
from db import get_db


@pytest.fixture
def app():
    return create_app()


def test_foreign_keys_enforced(app):
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute('DROP TABLE IF EXISTS child')
        cur.execute('DROP TABLE IF EXISTS parent')
        cur.execute('CREATE TABLE parent(id SERIAL PRIMARY KEY)')
        cur.execute('CREATE TABLE child(id SERIAL PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))')
        with pytest.raises(errors.ForeignKeyViolation):
            cur.execute('INSERT INTO child (parent_id) VALUES (999)')
        conn.rollback()
        cur.close()
        conn.close()

