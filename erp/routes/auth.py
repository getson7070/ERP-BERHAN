"""Authentication blueprint providing login, logout, and self-service signup."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import text

from erp.audit import log_audit
from erp.extensions import db, get_remote_address, limiter
from erp.models import (
    ClientRegistration,
    Employee,
    RegistrationInvite,
    Role,
    User,
    UserMFA,
    UserRoleAssignment,
)
from erp.services.mfa_service import verify_backup_code, verify_totp
from erp.services.session_service import (
    make_session_identifier,
    record_session,
    revoke_all_sessions_for_user,
    revoke_session,
)
from erp.utils import resolve_org_id

bp = Blueprint("auth", __name__, url_prefix="/auth")


# In-memory backoff for repeated failed logins
_FAILED_LOGINS: dict[str, tuple[int, datetime]] = {}


def _check_backoff(email: str) -> tuple[str, int]:
    """Return cooldown state for repeated login failures.

    Returns:
        ("ok", 0) when login is allowed.
        ("cooldown", seconds_remaining) when client must wait.
    """
    email = (email or "").lower()
    record = _FAILED_LOGINS.get(email)
    if not record:
        return "ok", 0

    attempts, locked_until = record
    now = datetime.now(UTC)
    if locked_until and locked_until > now:
        return "cooldown", int((locked_until - now).total_seconds())
    return "ok", 0


def _record_failure(email: str) -> None:
    """Record a failed login attempt and update cooldown."""
    email = (email or "").lower()
    attempts, _locked_until = _FAILED_LOGINS.get(email, (0, datetime.now(UTC)))
    attempts += 1

    # Simple linear backoff with upper bound:
    #  1st failure ~5s, 2nd ~10s, up to a max of 300s
    cooldown = min(300, max(5, attempts * 5))
    _FAILED_LOGINS[email] = (attempts, datetime.now(UTC) + timedelta(seconds=cooldown))


def _clear_failures(email: str) -> None:
    """Clear recorded failures after a successful login."""
    _FAILED_LOGINS.pop((email or "").lower(), None)


def _json_or_form(key: str, default: str = "") -> str:
    """Return a value from JSON or form payloads with safe defaults."""
    if request.is_json:
        payload: dict[str, Any] = request.get_json(silent=True) or {}
        return str(payload.get(key, default) or "").strip()
    return str(request.form.get(key, default) or "").strip()


def _login_rate_limit_key() -> str:
    """Key function that scopes login throttling to remote address + email."""
    email = _json_or_form("email", default="").lower().strip()
    return f"{get_remote_address()}:{email or 'anon'}"


def _assign_role(user: User, role_name: str) -> None:
    role = Role.query.filter_by(name=role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.flush()

    if not UserRoleAssignment.query.filter_by(user_id=user.id, role_id=role.id).first():
        db.session.add(UserRoleAssignment(user_id=user.id, role_id=role.id))


def _hash_invite(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _consume_invite(token: str, email: str, requested_role: str) -> RegistrationInvite | None:
    if not token:
        return None

    invite = RegistrationInvite.query.filter_by(token_hash=_hash_invite(token)).first()
    if invite is None:
        return None

    now = datetime.now(UTC)
    if invite.expires_at and invite.expires_at < now:
        return None
    if invite.uses_remaining <= 0:
        return None
    if invite.email and invite.email.lower() != email.lower():
        return None
    if invite.role and invite.role.lower() != requested_role:
        return None

    invite.uses_remaining -= 1
    db.session.add(invite)
    return invite


def _queue_registration_request(org_id: int, username: str, email: str, role: str) -> ClientRegistration:
    pending = ClientRegistration(
        org_id=org_id,
        name=username,
        email=email,
        status="pending",
    )
    db.session.add(pending)
    return pending


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", key_func=_login_rate_limit_key)
def login():
    """Authenticate a user via form or JSON payload and start a session."""
    # ---- GET: render login form or redirect authenticated users ----
    if request.method == "GET":
        if current_user.is_authenticated:
            # Already logged in → go to customizable dashboard
            return redirect(url_for("dashboard_customize.get_layout"))
        return render_template("login.html")

    # ---- POST: credential-based login ----
    email = _json_or_form("email").lower()
    password = _json_or_form("password")

    if not email or not password:
        flash("Email and password are required.", "danger")
        return render_template("login.html"), HTTPStatus.BAD_REQUEST

    # Check per-email cooldown (in addition to IP rate limiting)
    backoff_state, cooldown = _check_backoff(email)
    if backoff_state == "cooldown":
        message = f"Too many failed attempts. Try again in {cooldown} seconds."
        if request.is_json:
            return (
                jsonify(
                    {
                        "error": "too_many_attempts",
                        "retry_after": cooldown,
                    }
                ),
                HTTPStatus.TOO_MANY_REQUESTS,
            )
        flash(message, "danger")
        return render_template("login.html"), HTTPStatus.TOO_MANY_REQUESTS

    org_id = resolve_org_id()
    user = User.query.filter_by(email=email).first()

    # Invalid credentials → record failure + generic error
    if user is None or not user.check_password(password):
        _record_failure(email)
        flash("Invalid credentials.", "danger")
        if request.is_json:
            return jsonify({"error": "invalid_credentials"}), HTTPStatus.UNAUTHORIZED
        return render_template("login.html"), HTTPStatus.UNAUTHORIZED

    # Optional: account deactivation flag
    if hasattr(user, "is_active") and not getattr(user, "is_active", True):
        if request.is_json:
            return jsonify({"error": "account_inactive"}), HTTPStatus.FORBIDDEN
        flash("This account is deactivated.", "danger")
        return render_template("login.html"), HTTPStatus.FORBIDDEN

    # ---- MFA handling (TOTP / backup codes) ----
    mfa_row = UserMFA.query.filter_by(org_id=org_id, user_id=user.id).first()
    if mfa_row and mfa_row.is_enabled:
        totp_code = _json_or_form("totp")
        backup_code = _json_or_form("backup_code")

        if totp_code:
            if not verify_totp(mfa_row.totp_secret, totp_code):
                _record_failure(email)
                if request.is_json:
                    return (
                        jsonify({"error": "mfa_required_invalid_totp"}),
                        HTTPStatus.UNAUTHORIZED,
                    )
                flash("Multi-factor code is invalid.", "danger")
                return render_template("login.html"), HTTPStatus.UNAUTHORIZED
            mfa_row.last_used_at = datetime.now(UTC)
            db.session.add(mfa_row)

        elif backup_code:
            if not verify_backup_code(org_id, user.id, backup_code):
                _record_failure(email)
                if request.is_json:
                    return (
                        jsonify({"error": "mfa_required_invalid_backup"}),
                        HTTPStatus.UNAUTHORIZED,
                    )
                flash("Backup code is invalid or already used.", "danger")
                return render_template("login.html"), HTTPStatus.UNAUTHORIZED

        else:
            # MFA required but no code supplied
            if request.is_json:
                return jsonify({"error": "mfa_required"}), HTTPStatus.UNAUTHORIZED
            flash("Multi-factor authentication required. Enter your code.", "warning")
            return render_template("login.html"), HTTPStatus.UNAUTHORIZED

    # All checks passed – clear failure state
    _clear_failures(email)

    # Login + session registration
    login_user(user)
    session_id = session.get("session_id") or make_session_identifier()
    session["session_id"] = session_id
    record_session(org_id, user.id, session_id)

    # Audit trail for success
    try:
        log_audit(
            user.id,
            org_id,
            "auth.login",
            f"ip={get_remote_address()} session_id={session_id}",
        )
    except Exception:
        # Audit failures must never break login
        pass

    next_url = request.args.get("next")
    if not next_url or urlparse(next_url).netloc:
        next_url = url_for("analytics.dashboard_snapshot")

    if request.is_json:
        return jsonify({"user_id": user.id, "redirect": next_url}), HTTPStatus.OK

    flash("Signed in successfully.", "success")
    return redirect(next_url)


@bp.post("/logout")
@login_required
def logout():
    """Terminate the active session."""
    org_id = resolve_org_id()
    session_id = session.get("session_id")

    if session_id:
        revoke_session(org_id, session_id, getattr(current_user, "id", None))
        session.pop("session_id", None)

    # Audit logout event (best-effort)
    try:
        log_audit(
            getattr(current_user, "id", None),
            org_id,
            "auth.logout",
            f"session_id={session_id}",
        )
    except Exception:
        pass

    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@bp.post("/register")
@limiter.limit("5 per minute")
def register():
    """Self-service signup used by the UI and tests to seed new users."""

    email = _json_or_form("email").lower()
    password = _json_or_form("password")
    username = _json_or_form("username") or email.split("@", 1)[0]
    role = (_json_or_form("role") or "employee").lower()
    invite_code = _json_or_form("invite_code")
    org_id = resolve_org_id()
    expects_json = request.is_json
    allowed_roles = set(current_app.config.get("SELF_REGISTRATION_ALLOWED_ROLES", ("employee",)))
    privileged_roles = set(current_app.config.get("PRIVILEGED_ROLES", ("admin",)))
    mode = current_app.config.get("SELF_REGISTRATION_MODE", "invite-only").lower()

    if role not in allowed_roles:
        message = "Requested role is not available for self-service onboarding."
        if expects_json:
            return jsonify({"error": "role_not_allowed"}), HTTPStatus.FORBIDDEN
        flash(message, "danger")
        return redirect(url_for("auth.login")), HTTPStatus.FORBIDDEN

    if not email or not password:
        if expects_json:
            return (
                jsonify({"error": "email_and_password_required"}),
                HTTPStatus.BAD_REQUEST,
            )
        flash("Email and password are required to register.", "danger")
        return redirect(url_for("auth.login")), HTTPStatus.BAD_REQUEST

    existing = User.query.filter_by(email=email).first()
    if existing:
        if expects_json:
            return jsonify({"error": "user_exists"}), HTTPStatus.CONFLICT
        flash("An account already exists for that email.", "warning")
        return redirect(url_for("auth.login")), HTTPStatus.CONFLICT

    pending_exists = bool(
        db.session.execute(
            text(
                "SELECT 1 FROM client_registrations "
                "WHERE email = :email AND status = 'pending' LIMIT 1"
            ),
            {"email": email},
        ).scalar()
    )

    invite = None
    if invite_code:
        invite = _consume_invite(invite_code, email, role)
        if invite is None:
            if expects_json:
                return jsonify({"error": "invalid_invite"}), HTTPStatus.FORBIDDEN
            flash("That invite link has expired or is invalid.", "danger")
            return redirect(url_for("auth.login")), HTTPStatus.FORBIDDEN

    if mode in {"invite-only", "request-only"} and invite is None:
        if pending_exists:
            if expects_json:
                return (
                    jsonify({"status": "pending", "message": "Awaiting administrator approval."}),
                    HTTPStatus.ACCEPTED,
                )
            flash("Your original request is still pending review.", "info")
            return redirect(url_for("auth.login")), HTTPStatus.ACCEPTED
        _queue_registration_request(org_id, username, email, role)
        db.session.commit()
        if expects_json:
            return (
                jsonify({"status": "pending", "message": "Awaiting administrator approval."}),
                HTTPStatus.ACCEPTED,
            )
        flash("Your request has been queued for administrator approval.", "info")
        return redirect(url_for("auth.login")), HTTPStatus.ACCEPTED

    if role in privileged_roles:
        if pending_exists:
            if expects_json:
                return (
                    jsonify(
                        {
                            "status": "pending",
                            "message": "Privileged roles require MFA + manual approval.",
                        }
                    ),
                    HTTPStatus.ACCEPTED,
                )
            flash("Privileged roles require MFA and a security review. Request submitted.", "warning")
            return redirect(url_for("auth.login")), HTTPStatus.ACCEPTED
        _queue_registration_request(org_id, username, email, role)
        db.session.commit()
        if expects_json:
            return (
                jsonify(
                    {
                        "status": "pending",
                        "message": "Privileged roles require MFA + manual approval.",
                    }
                ),
                HTTPStatus.ACCEPTED,
            )
        flash("Privileged roles require MFA and a security review. Request submitted.", "warning")
        return redirect(url_for("auth.login")), HTTPStatus.ACCEPTED

    user = User(username=username, email=email)
    # Relies on User.password setter to hash properly
    user.password = password
    db.session.add(user)
    db.session.flush()

    employee = Employee(
        organization_id=org_id,
        first_name=username,
        last_name="",
        email=email,
        role=role,
    )
    db.session.add(employee)

    _assign_role(user, role)
    db.session.commit()

    log_audit(user.id, org_id, "user.registered", f"role={role}")

    login_user(user)
    if expects_json:
        return (
            jsonify({"user_id": user.id, "role": role, "org_id": org_id, "status": "active"}),
            HTTPStatus.CREATED,
        )

    flash("Account activated via verified invite.", "success")
    return redirect(url_for("analytics.dashboard_snapshot")), HTTPStatus.CREATED
