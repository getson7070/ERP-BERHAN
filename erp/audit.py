from datetime import datetime, UTC
import hashlib
from db import get_db
from erp import AUDIT_CHAIN_BROKEN


def log_audit(user_id: int | None, org_id: int | None, action: str, details: str = "") -> None:
    """Record an auditable event with hash-chaining for tamper evidence."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT hash FROM audit_logs ORDER BY id DESC LIMIT 1")
    prev = cur.fetchone()
    prev_hash = prev[0] if prev else ""
    timestamp = datetime.now(UTC)
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


def check_audit_chain() -> int:
    """Verify hash-chain integrity for all audit log rows.

    Returns the number of breaks detected and increments the
    ``audit_chain_broken_total`` Prometheus counter accordingly.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, org_id, action, details, prev_hash, hash, created_at FROM audit_logs ORDER BY id"
    )
    prev_hash = ""
    breaks = 0
    rows = cur.fetchall()
    for row in rows:
        (
            _id,
            user_id,
            org_id,
            action,
            details,
            row_prev_hash,
            current_hash,
            created_at,
        ) = row
        created_at_str = created_at if isinstance(created_at, str) else created_at.isoformat()
        dt = datetime.fromisoformat(created_at_str)
        expected_hash = hashlib.sha256(
            f"{prev_hash}{user_id}{org_id}{action}{details}{dt.isoformat()}".encode()
        ).hexdigest()
        if row_prev_hash != prev_hash or current_hash != expected_hash:
            breaks += 1
        prev_hash = current_hash
    cur.close()
    conn.close()
    if breaks:
        AUDIT_CHAIN_BROKEN.inc(breaks)
    return breaks
