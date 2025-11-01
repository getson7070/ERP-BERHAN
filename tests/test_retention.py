import os
import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from erp.data_retention import purge_expired_records, anonymize_users  # noqa: E402
from db import get_db  # noqa: E402


def _init_db(tmp_path: Path) -> None:
    os.environ["DATABASE_PATH"] = str(tmp_path / "retention.db")
    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, active INTEGER, anonymized INTEGER DEFAULT 0, retain_until TIMESTAMP)"
    )
    conn.execute(
        "CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, retain_until TIMESTAMP, created_at TIMESTAMP)"
    )
    conn.commit()
    conn.close()


def test_purge_expired_records(tmp_path):
    _init_db(tmp_path)
    conn = get_db()
    conn.execute(
        "INSERT INTO users (email, active, anonymized, retain_until) VALUES ('old@x',1,0,'2000-01-01'), ('new@x',1,0,'2999-01-01')"
    )
    conn.execute(
        "INSERT INTO audit_logs (action, retain_until, created_at) VALUES ('old','2000-01-01','1999-01-01'), ('new','2999-01-01','1999-01-01')"
    )
    conn.commit()
    conn.close()
    purge_expired_records()
    conn = get_db()
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0] == 1
    conn.close()


def test_anonymize_users(tmp_path):
    _init_db(tmp_path)
    conn = get_db()
    conn.execute(
        "INSERT INTO users (email, active, anonymized, retain_until) VALUES ('user@x',0,0,'2000-01-01')"
    )
    conn.commit()
    conn.close()
    anonymize_users()
    conn = get_db()
    email, flag = conn.execute("SELECT email, anonymized FROM users").fetchone()
    assert flag == 1 and len(email) == 64
    conn.close()


