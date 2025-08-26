from datetime import datetime
import hashlib
from db import get_db


def log_audit(user_id: int | None, org_id: int | None, action: str, details: str = "") -> None:
    """Record an auditable event with hash-chaining for tamper evidence."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT hash FROM audit_logs ORDER BY id DESC LIMIT 1")
    prev = cur.fetchone()
    prev_hash = prev[0] if prev else ""
    timestamp = datetime.utcnow()
    record = f"{prev_hash}{user_id}{org_id}{action}{details}{timestamp.isoformat()}"
    current_hash = hashlib.sha256(record.encode()).hexdigest()
    try:
        cur.execute(
            "INSERT INTO audit_logs (user_id, org_id, action, details, prev_hash, hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, org_id, action, details, prev_hash, current_hash, timestamp),
        )
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()
