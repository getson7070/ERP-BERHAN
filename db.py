import os
import sqlite3

DATABASE_PATH = os.environ.get('DATABASE_PATH', 'erp.db')

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn
