import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("DATABASE_URL", "erp.db")

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()
