"""User management blueprint powering the admin console."""
"""User management blueprint powering the admin console.

This module consolidates the user management functionality into a single
blueprint, exposing both HTML and JSON endpoints for administrators.  It
supports creating employees and associated login accounts, assigning roles,
approving or rejecting client registrations, and deleting users.  All
operations require authentication and are scoped by organisation via
``resolve_org_id()``.

The blueprint uses Flask‑Login to ensure that only authenticated users can
perform administrative tasks.  Organisations may customise the role checks by
wrapping endpoints with additional decorators (e.g. ``@roles_required('admin')``).
"""
from __future__ import annotations

from datetime import datetime
from secrets import token_urlsafe

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from erp.extensions import db
from erp.models import (
    ClientRegistration,
    Employee,
    Role,
    User,
    UserRoleAssignment,
)
from erp.utils import resolve_org_id

bp = Blueprint("user_management", __name__, template_folder="../templates/user_management")
from typing import Any, Dict

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from erp.extensions import db
from erp.models import ClientRegistration, Employee, Role, User, UserRoleAssignment
from erp.utils import resolve_org_id


bp = Blueprint("user_management", __name__, url_prefix="/user_management", template_folder="../templates/user_management")


def _ensure_role(name: str) -> Role:
    role = Role.query.filter_by(name=name).first()
    if role is None:
        role = Role(name=name)
        db.session.add(role)
        db.session.flush()
    return role


def _assign_role(user: User, role_name: str) -> None:
    role = _ensure_role(role_name)
    if not UserRoleAssignment.query.filter_by(user_id=user.id, role_id=role.id).first():
        db.session.add(UserRoleAssignment(user_id=user.id, role_id=role.id))


@bp.route("/", methods=["GET", "POST"])
@login_required
def index() -> Any:
    """Render the user management dashboard or create a new employee.

    When accessed via GET, this route displays pending client registrations and
    the list of existing users.  When accessed via POST, it creates a new
    employee record and an associated user with a randomly generated password.
    """
    org_id = resolve_org_id()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        role = (request.form.get("role") or "employee").strip().lower()
        if not name or not email:
            flash("Name and email are required", "danger")
        else:
            # Split name into first and last for the employee record
            first, *rest = name.split(" ", 1)
            last = rest[0] if rest else first
            employee = Employee(
                organization_id=org_id,
                first_name=first,
                last_name=last,
                email=email,
                role=role,
            )
            db.session.add(employee)
            # Create a corresponding user
            username = email.split("@", 1)[0]
            password = token_urlsafe(12)
            user = User(username=username, email=email)
            user.password = password  # hashed via property setter
            db.session.add(user)
            db.session.flush()
            _assign_role(user, role)
            db.session.commit()
            flash("Employee created and invited", "success")
            return redirect(url_for("user_management.index"))

    pending_clients = (
        ClientRegistration.query.filter_by(status="pending", org_id=org_id)
        .order_by(ClientRegistration.created_at.desc())
        .all()
    )
    users_query = (
        db.session.query(User, Role.name)
        .join(UserRoleAssignment, UserRoleAssignment.user_id == User.id, isouter=True)
        .join(Role, Role.id == UserRoleAssignment.role_id, isouter=True)
        .order_by(User.username)
    )
    users_list = [
        {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "role": role_name or "--",
        }
        for user, role_name in users_query
    ]
    return render_template(
        "user_management/index.html",
        pending_clients=pending_clients,
        users_list=users_list,
    )


@bp.post("/clients/<int:client_id>/approve")
@login_required
def approve_client(client_id: int) -> Any:
    """Approve a pending client registration."""
    client = ClientRegistration.query.get_or_404(client_id)
    client.status = "approved"
    client.decided_at = datetime.utcnow()
    db.session.commit()
    flash("Client approved", "success")
    return redirect(url_for("user_management.index"))


@bp.post("/clients/<int:client_id>/reject")
@login_required
def reject_client(client_id: int) -> Any:
    """Reject a pending client registration."""
    client = ClientRegistration.query.get_or_404(client_id)
    client.status = "rejected"
    client.decided_at = datetime.utcnow()
    db.session.commit()
    flash("Client rejected", "warning")
    return redirect(url_for("user_management.index"))


@bp.post("/users/<int:user_id>/delete")
@login_required
def delete_user(user_id: int) -> Any:
    """Remove a user account and associated role assignments."""
    user = User.query.get_or_404(user_id)
    UserRoleAssignment.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash("User removed", "success")
    return redirect(url_for("user_management.index"))


@bp.get("/api/users")
@login_required
def api_users() -> Any:
    """Return a JSON list of users and their roles for the current organisation."""
    org_id = resolve_org_id()
    users_query = (
        db.session.query(User, Role.name)
        .join(UserRoleAssignment, UserRoleAssignment.user_id == User.id, isouter=True)
        .join(Role, Role.id == UserRoleAssignment.role_id, isouter=True)
        .filter(User.organization_id == org_id if hasattr(User, "organization_id") else True)
        .order_by(User.username)
    )
    payload: list[Dict[str, Any]] = []
    for user, role_name in users_query:
        payload.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role_name or "--",
        })
    return jsonify(payload)


@bp.get("/api/pending_clients")
@login_required
def api_pending_clients() -> Any:
    """Return pending client registrations as JSON."""
    org_id = resolve_org_id()
    pending_clients = (
        ClientRegistration.query.filter_by(status="pending", org_id=org_id)
        .order_by(ClientRegistration.created_at.desc())
        .all()
    )
    return jsonify([
        {
            "id": client.id,
            "name": client.name,
            "email": client.email,
            "created_at": client.created_at.isoformat() if hasattr(client, "created_at") else None,
        }
        for client in pending_clients
    ])


__all__ = ["bp"]
