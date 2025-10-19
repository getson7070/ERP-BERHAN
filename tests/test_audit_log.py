import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp.audit import log_audit, check_audit_chain
from db import get_db
from prometheus_client import REGISTRY, generate_latest
from erp import AUDIT_CHAIN_BROKEN


def test_log_audit_writes_entry(tmp_path, monkeypatch):
    db_file = tmp_path / "audit.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    conn = get_db()
    conn.execute(
        "CREATE TABLE audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, org_id INTEGER, action TEXT, details TEXT, prev_hash TEXT, hash TEXT, created_at TIMESTAMP)"
    )
    conn.commit()
    log_audit(1, 1, "test", "details")
    cur = conn.execute("SELECT action, details, prev_hash, hash FROM audit_logs")
    row = cur.fetchone()
    assert row[0:2] == ("test", "details")
    assert len(row[3]) == 64
    conn.close()


def test_audit_chain_checker(monkeypatch, tmp_path):
    db_file = tmp_path / "audit.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    conn = get_db()
    conn.execute(
        "CREATE TABLE audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, org_id INTEGER, action TEXT, details TEXT, prev_hash TEXT, hash TEXT, created_at TIMESTAMP)"
    )
    conn.commit()
    log_audit(1, 1, "a")
    log_audit(1, 1, "b")
    conn.execute("UPDATE audit_logs SET hash='bad' WHERE id=2")
    conn.commit()
    AUDIT_CHAIN_BROKEN._value.set(0)
    breaks = check_audit_chain()
    assert breaks == 1
    metrics = generate_latest(REGISTRY)
    assert b"audit_chain_broken_total 1.0" in metrics
    conn.close()


