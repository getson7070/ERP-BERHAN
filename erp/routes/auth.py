"""Authentication blueprint providing login, logout, and self-service signup."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
import re
from secrets import token_urlsafe
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
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp
from werkzeug.security import generate_password_hash

from erp.audit import log_audit
from erp.extensions import db, get_remote_address, limiter
from erp.models import (
    ClientRegistration,
    ClientAccount,
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


def _get_role_names(user: Any) -> set[str]:
    """Extract normalized role names from the user model for MFA decisions."""

    roles: set[str] = set()
    if not user:
        return roles

    # Relationship collection
    rel = getattr(user, "roles", None)
    if rel:
        for r in rel:
            name = getattr(r, "name", None)
            if name:
                roles.add(str(name).lower())

    # Fallback single-value attributes
    for attr in ("role", "role_name"):
        val = getattr(user, attr, None)
        if isinstance(val, str):
            roles.add(val.lower())

    return roles


class ClientRegistrationForm(FlaskForm):
    tin = StringField(
        "TIN",
        validators=[
            DataRequired(),
            Length(min=10, max=10, message="TIN must be exactly 10 digits"),
            Regexp(r"^\d{10}$", message="TIN must be 10 digits"),
        ],
    )
    institution_name = StringField("Institution name", validators=[DataRequired(), Length(max=255)])
    contact_name = StringField("Contact name", validators=[DataRequired(), Length(max=255)])
    contact_position = StringField("Position", validators=[DataRequired(), Length(max=128)])
    email = StringField("Work email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[DataRequired(), Length(max=64)])
    region = StringField("Region", validators=[DataRequired(), Length(max=128)])
    zone = StringField("Zone", validators=[Optional(), Length(max=128)])
    city = StringField("City", validators=[DataRequired(), Length(max=128)])
    subcity = StringField("Sub-city/Woreda", validators=[Optional(), Length(max=128)])
    woreda = StringField("Woreda", validators=[Optional(), Length(max=128)])
    kebele = StringField("Kebele", validators=[Optional(), Length(max=128)])
    street = StringField("Street", validators=[Optional(), Length(max=255)])
    house_number = StringField("House number", validators=[Optional(), Length(max=64)])
    gps_hint = StringField("GPS / landmark", validators=[Optional(), Length(max=255)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])
    password = PasswordField("Portal password", validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField("Submit registration")


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
        institution_name=username,
        contact_name=username,
        email=email,
        tin=f"EMP-{int(datetime.now(UTC).timestamp())}-{token_urlsafe(4)}",
        status="pending",
    )
    db.session.add(pending)
    return pending


@bp.route("/client/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def client_register():
    """Capture client onboarding requests with rich institution metadata."""

    form = ClientRegistrationForm()
    if form.validate_on_submit():
        org_id = resolve_org_id()
        email = (form.email.data or "").lower()
        tin = (form.tin.data or "").strip()

        # Server-side enforcement beyond WTForms to guarantee 10-digit TINs and
        # avoid relying solely on client validation.
        if not re.fullmatch(r"\d{10}", tin):
            flash("TIN must be a 10 digit number.", "danger")
            return render_template("client_registration.html", form=form), HTTPStatus.BAD_REQUEST

        existing_account = ClientAccount.query.filter_by(org_id=org_id, email=email).first()
        if existing_account:
            flash("An account with that email already exists.", "warning")
            return redirect(url_for("auth.login"))

        duplicate_contact = ClientRegistration.query.filter_by(
            org_id=org_id, tin=tin, email=email
        ).first()
        if duplicate_contact and duplicate_contact.status == "pending":
            flash(
                "A registration for this institution and contact is already pending review.",
                "info",
            )
            return redirect(url_for("auth.login"))
        if duplicate_contact and duplicate_contact.status == "approved":
            flash(
                "This contact is already approved for the institution. Please sign in or reset your password.",
                "info",
            )
            return redirect(url_for("auth.login"))

        existing_institution = (
            db.session.execute(
                text(
                    "SELECT id FROM institutions WHERE org_id = :org_id AND tin = :tin LIMIT 1"
                ),
                {"org_id": org_id, "tin": tin},
            ).scalar()
            is not None
        )
        is_additional_contact = existing_institution
        if existing_institution:
            flash(
                "TIN found: this submission will be reviewed as an additional contact for the existing institution.",
                "info",
            )

        registration = ClientRegistration(
            org_id=org_id,
            institution_name=form.institution_name.data.strip(),
            contact_name=form.contact_name.data.strip(),
            contact_position=form.contact_position.data.strip(),
            email=email,
            phone=form.phone.data.strip(),
            tin=tin,
            region=form.region.data.strip() if form.region.data else None,
            zone=form.zone.data.strip() if form.zone.data else None,
            city=form.city.data.strip() if form.city.data else None,
            subcity=form.subcity.data.strip() if form.subcity.data else None,
            woreda=form.woreda.data.strip() if form.woreda.data else None,
            kebele=form.kebele.data.strip() if form.kebele.data else None,
            street=form.street.data.strip() if form.street.data else None,
            house_number=form.house_number.data.strip() if form.house_number.data else None,
            gps_hint=form.gps_hint.data.strip() if form.gps_hint.data else None,
            notes=form.notes.data.strip() if form.notes.data else None,
            password_hash=generate_password_hash(form.password.data),
            status="pending",
        )
        db.session.add(registration)
        db.session.commit()

        try:
            log_audit(
                None,
                org_id,
                "auth.client_register",
                f"tin={tin} email={email} additional_contact={is_additional_contact}",
            )
        except Exception:
            # Registration should not fail if audit logging encounters an error.
            pass
        success_message = (
            "Registration submitted as an additional contact. A supervisor will link you to the institution."
            if is_additional_contact
            else "Registration submitted. A supervisor will approve your access."
        )
        flash(success_message, "success")
        return redirect(url_for("auth.login"))

    return render_template("client_registration.html", form=form)


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

    # Reset MFA session markers on every login attempt
    session.pop("mfa_verified", None)

    privileged_roles = {
        r.lower() for r in current_app.config.get("MFA_REQUIRED_ROLES", ())
    }

    user_roles = _get_role_names(user)
    mfa_required_for_role = bool(user_roles & privileged_roles)

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

    if mfa_required_for_role and not (mfa_row and mfa_row.is_enabled):
        message = "Admins and supervisors must enroll MFA before signing in."
        if request.is_json:
            return jsonify({"error": "mfa_enrollment_required"}), HTTPStatus.FORBIDDEN
        flash(message, "danger")
        return render_template("login.html"), HTTPStatus.FORBIDDEN

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

        session["mfa_verified"] = True
    else:
        # No MFA configured; mark session verified only when role does not
        # mandate MFA.
        session["mfa_verified"] = not mfa_required_for_role

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

    user = User(username=username, email=email, org_id=org_id)
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
