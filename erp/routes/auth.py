# erp/routes/auth.py
from __future__ import annotations

from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user

from erp.extensions import db, login_manager
from erp.models import User, DeviceAuthorization
from erp.security.device import read_device_id  # uses header/query/cookie helper

bp = Blueprint("auth", __name__, url_prefix="/auth")

# -----------------------
# Login view
# -----------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Login for three roles: client / employee / admin
    - GET: render login form
    - POST: authenticate; enforce device allowlist for employee/admin
    """
    role = (request.args.get("role") or "client").strip().lower()
    if role not in ("client", "employee", "admin"):
        role = "client"

    if request.method == "GET":
        # Just render the form with role context
        return render_template("auth/login.html", role=role)

    # POST: authenticate
    identifier = (request.form.get("email") or request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""

    if not identifier or not password:
        flash("Username/Email and password are required.", "error")
        return render_template("auth/login.html", role=role), 400

    # Look up by username OR email, constrained to role and active
    user = (
        User.query.filter(
            db.and_(
                db.or_(User.username.ilike(identifier), User.email.ilike(identifier)),
                User.role == role,
                User.is_active.is_(True),
            )
        )
        .first()
    )

    if not user or not user.check_password(password):
        flash("Invalid credentials.", "error")
        return render_template("auth/login.html", role=role), 401

    # Device enforcement:
    # - Client is public (no device gate)
    # - Employee/Admin require device to be in allowlist
    if role in ("employee", "admin"):
        device_id = read_device_id(request) or request.cookies.get("device")
        if not device_id:
            flash("This login requires a registered device. No device ID found.", "error")
            return render_template("auth/login.html", role=role), 403

        if not _is_device_allowed(device_id, user):
            flash("This device is not authorized for your account.", "error")
            return render_template("auth/login.html", role=role), 403

    # All good, log user in
    login_user(user, remember=True)

    # Where to next
    nxt = request.args.get("next")
    if nxt:
        return redirect(nxt)

    # If you later create dashboards per role, swap these URLs accordingly.
    # For now, return to the chooser; the tiles will reflect device status.
    return redirect(url_for("main.choose_login"))


# -----------------------
# Logout + debug
# -----------------------
@bp.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    flash("Signed out.", "success")
    return redirect(url_for("main.choose_login"))


@bp.route("/whoami", methods=["GET"])
def whoami():
    """
    Tiny diagnostic endpoint; safe to keep in production (no secrets).
    """
    if current_user.is_authenticated:
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
        }, 200
    return {"anonymous": True}, 200


# -----------------------
# Helpers
# -----------------------
def _is_device_allowed(device_id: str, user: User) -> bool:
    """
    A device is allowed if ANY of these exist with allowed=True:
      1) Specific to this user
      2) Role-wide allowlist (same role as user; user_id is NULL)
      3) Global allowlist (no user_id and no role)
    """
    q = DeviceAuthorization.query.filter(
        db.and_(
            DeviceAuthorization.device_id == device_id,
            DeviceAuthorization.allowed.is_(True),
            db.or_(
                DeviceAuthorization.user_id == user.id,                           # user-specific
                db.and_(DeviceAuthorization.user_id.is_(None),
                        DeviceAuthorization.role == user.role),                   # role-wide
                db.and_(DeviceAuthorization.user_id.is_(None),
                        DeviceAuthorization.role.is_(None)),                      # global
            ),
        )
    )
    return db.session.query(q.exists()).scalar()
