from flask import current_app
from sqlalchemy import text
from db import get_db

def log_audit(user_id, org_id, action: str, details: str = "") -> None:
    try:
        conn = get_db()
        conn.execute(
            text("INSERT INTO audit_logs (user_id, org_id, action, details) VALUES (:u, :o, :a, :d)"),
            {"u": user_id, "o": org_id, "a": action, "d": details},
        )
        conn.commit()
        conn.close()
    except Exception as e:
        current_app.logger.warning("audit_log_failed: %s", e)
