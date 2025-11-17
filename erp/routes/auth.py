"""Authentication blueprint providing login, logout, and self-service signup."""
from __future__ import annotations

from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from erp.extensions import db
from erp.models import Employee, Role, User, UserRoleAssignment
from erp.utils import resolve_org_id

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _json_or_form(key: str, default: str = "") -> str:
    """Return a value from JSON or form payloads with safe defaults."""

    if request.is_json:
        payload: dict[str, Any] = request.get_json(silent=True) or {}
        return str(payload.get(key, default) or "").strip()
    return str(request.form.get(key, default) or "").strip()


def _assign_role(user: User, role_name: str) -> None:
    role = Role.query.filter_by(name=role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.flush()

    if not UserRoleAssignment.query.filter_by(user_id=user.id, role_id=role.id).first():
        db.session.add(UserRoleAssignment(user_id=user.id, role_id=role.id))


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a user via form or JSON payload and start a session."""

    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("dashboard_customize.index"))
        return render_template("login.html")

    email = _json_or_form("email").lower()
    password = _json_or_form("password")
    if not email or not password:
        flash("Email and password are required.", "danger")
        return render_template("login.html"), HTTPStatus.BAD_REQUEST

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        flash("Invalid credentials.", "danger")
        if request.is_json:
            return jsonify({"error": "invalid_credentials"}), HTTPStatus.UNAUTHORIZED
        return render_template("login.html"), HTTPStatus.UNAUTHORIZED

    login_user(user)
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

    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@bp.post("/register")
def register():
    """Self-service signup used by the UI and tests to seed new users."""

    email = _json_or_form("email").lower()
    password = _json_or_form("password")
    username = _json_or_form("username") or email.split("@", 1)[0]
    role = _json_or_form("role") or "employee"
    org_id = resolve_org_id()
    expects_json = request.is_json

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

    user = User(username=username, email=email)
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

    login_user(user)
    if expects_json:
        return (
            jsonify({"user_id": user.id, "role": role, "org_id": org_id}),
            HTTPStatus.CREATED,
        )

    flash("Account request submitted.", "success")
    return redirect(url_for("analytics.dashboard_snapshot")), HTTPStatus.CREATED
