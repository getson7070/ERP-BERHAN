from functools import wraps
from flask import session, abort
from db import get_db
from sqlalchemy import text


def get_workflow(module):
    """Return (enabled, steps_json) for module in current org."""
    conn = get_db()
    cur = conn.execute(
        text('SELECT enabled, steps FROM workflows WHERE org_id = :org AND module = :mod'),
        {'org': session.get('org_id'), 'mod': module}
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0], row[1]
    return True, '[]'


def require_enabled(module):
    """Decorator to block access when a module is disabled in workflows table."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            enabled, _ = get_workflow(module)
            if not enabled:
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator
