from datetime import datetime
from db import get_db


def log_audit(user_id: int | None, org_id: int | None, action: str, details: str = "") -> None:
    """Record an auditable event with optional user and org context."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO audit_logs (user_id, org_id, action, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, org_id, action, details, datetime.utcnow()),
        )
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()
