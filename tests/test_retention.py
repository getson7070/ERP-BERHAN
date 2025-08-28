import sqlite3
from datetime import datetime, UTC, timedelta

from erp.data_retention import purge_expired_rows, anonymize_users


def setup_db():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, delete_after TIMESTAMP, created_at TIMESTAMP)"
    )
    conn.execute(
        "CREATE TABLE invoices (id INTEGER PRIMARY KEY, delete_after TIMESTAMP, issued_at TIMESTAMP)"
    )
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, active INTEGER, anonymized INTEGER DEFAULT 0)"
    )
    now = datetime.now(UTC)
    past = now - timedelta(days=1)
    future = now + timedelta(days=1)
    conn.execute(
        "INSERT INTO audit_logs (delete_after, created_at) VALUES (?, ?)", (past, past)
    )
    conn.execute(
        "INSERT INTO audit_logs (delete_after, created_at) VALUES (?, ?)",
        (future, future),
    )
    conn.execute(
        "INSERT INTO invoices (delete_after, issued_at) VALUES (?, ?)", (past, past)
    )
    conn.execute(
        "INSERT INTO invoices (delete_after, issued_at) VALUES (?, ?)", (future, future)
    )
    conn.execute(
        "INSERT INTO users (email, active, anonymized) VALUES ('a@example.com',0,0)"
    )
    conn.commit()
    return conn


def test_purge_and_anonymize(monkeypatch):
    conn = setup_db()
    import db
    import erp.data_retention as dr

    class Wrapper:
        def __init__(self, inner):
            self._inner = inner

        def __getattr__(self, name):
            return getattr(self._inner, name)

        def close(self):  # pragma: no cover - test helper
            pass

    wrapper = Wrapper(conn)
    monkeypatch.setattr(db, "get_db", lambda: wrapper)
    monkeypatch.setattr(dr, "get_db", lambda: wrapper)

    purged = purge_expired_rows()
    assert purged == 2
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM audit_logs")
    assert cur.fetchone()[0] == 1

    anonymized = anonymize_users()
    assert anonymized == 1
    cur.execute("SELECT email, anonymized FROM users")
    email, flag = cur.fetchone()
    assert flag == 1 and len(email) == 64
