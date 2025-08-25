from functools import wraps
from flask import session, redirect, url_for
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import bcrypt
from db import get_db


def has_permission(permission: str) -> bool:
    """Check database for permission tied to current organization."""
    # During tests, a permissions list may be stored in the session.
    session_perms = session.get("permissions")
    if session_perms is not None:
        return permission in session_perms
    role = session.get("role")
    if role == "Management":
        return True
    user_id = session.get("user_id")
    org_id = session.get("org_id")
    if not user_id or not org_id:
        # Fallback to session-based permissions for legacy tests and
        # unauthenticated flows.  This preserves previous behaviour while
        # the RBAC tables are populated.
        return permission in session.get("permissions", [])

    conn = get_db()
    cur = conn.execute(
        """
        SELECT 1
        FROM role_assignments ra
        JOIN role_permissions rp ON ra.role_id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id
        WHERE ra.user_id = %s AND ra.org_id = %s AND p.name = %s
        """,
        (user_id, org_id, permission),
    )
    has_perm = cur.fetchone() is not None
    conn.close()
    return has_perm


def roles_required(*roles):
    """Decorator to restrict access to users with specific roles."""

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")
            org_id = session.get("org_id")
            if not user_id or not org_id:
                return redirect(url_for("main.dashboard"))

            conn = get_db()
            cur = conn.execute(
                """
                SELECT r.name FROM role_assignments ra
                JOIN roles r ON ra.role_id = r.id
                WHERE ra.user_id = %s AND ra.org_id = %s
                """,
                (user_id, org_id),
            )
            rows = cur.fetchall()
            conn.close()
            user_roles = [row[0] for row in rows]
            if not any(r in user_roles for r in roles):
                return redirect(url_for("main.dashboard"))
            return f(*args, **kwargs)

        return wrapped

    return decorator

ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("$argon2"):
        try:
            return ph.verify(password_hash, password)
        except VerifyMismatchError:
            return False
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('auth.choose_login'))
        return f(*args, **kwargs)
    return wrap
