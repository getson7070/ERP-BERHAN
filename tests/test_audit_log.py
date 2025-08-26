import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from erp.audit import log_audit
from db import get_db


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
