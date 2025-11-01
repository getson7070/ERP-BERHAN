import sqlite3

from erp.audit import log_audit, check_audit_chain


def test_audit_hash_chain(tmp_path, monkeypatch):
    db_path = tmp_path / "audit.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            org_id INTEGER,
            action TEXT,
            details TEXT,
            prev_hash TEXT,
            hash TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    log_audit(1, 1, "create")
    log_audit(1, 1, "update")
    assert check_audit_chain() == 0
    tamper = sqlite3.connect(db_path)
    tamper.execute("UPDATE audit_logs SET action='tampered' WHERE id=2")
    tamper.commit()
    tamper.close()
    assert check_audit_chain() == 1


