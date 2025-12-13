"""User management blueprint powering the admin console."""
from __future__ import annotations

from datetime import UTC, datetime
from secrets import token_urlsafe

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from erp.security_decorators_phase2 import require_permission
from erp.extensions import db
from erp.models import (
    ClientAccount,
    ClientRegistration,
    ClientRoleAssignment,
    Employee,
    Institution,
    Role,
    User,
    UserRoleAssignment,
)
from erp.services.client_auth_utils import set_password
from erp.utils import resolve_org_id

bp = Blueprint("user_management", __name__, template_folder="../templates/user_management")


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


def _assign_client_role(account: ClientAccount, role_name: str) -> None:
    role = _ensure_role(role_name)
    if not ClientRoleAssignment.query.filter_by(
        client_account_id=account.id, role_id=role.id
    ).first():
        db.session.add(ClientRoleAssignment(client_account_id=account.id, role_id=role.id))


@bp.route("/", methods=["GET", "POST"])
@require_permission("admin_console", "view")
def index():
    org_id = resolve_org_id()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        role = (request.form.get("role") or "employee").strip()
        if not name or not email:
            flash("Name and email are required", "danger")
        else:
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

            username = email.split("@", 1)[0]
            password = token_urlsafe(12)
            user = User(
                org_id=org_id,
                username=username,
                email=email,
                full_name=name,
                is_active=True,
            )
            set_password(user, password)
            db.session.add(user)
            db.session.flush()

            _assign_role(user, role)
            db.session.commit()
            flash(
                f"User created: {username}. Temporary password: {password}",
                "success",
            )
            return redirect(url_for("user_management.index"))

    pending_clients = (
        ClientRegistration.query.filter_by(status="pending", org_id=org_id)
        .order_by(ClientRegistration.created_at.asc())
        .all()
    )
    users = User.query.filter_by(org_id=org_id).order_by(User.id.desc()).limit(200).all()
    employees = Employee.query.filter_by(organization_id=org_id).order_by(Employee.id.desc()).limit(200).all()
    institutions = Institution.query.filter_by(org_id=org_id).order_by(Institution.id.desc()).limit(200).all()

    return render_template(
        "user_management/index.html",
        pending_clients=pending_clients,
        users=users,
        employees=employees,
        institutions=institutions,
    )


@bp.post("/clients/<int:client_id>/approve")
@require_permission("clients", "approve")
def approve_client(client_id: int):
    client = ClientRegistration.query.get_or_404(client_id)
    if client.status != "pending":
        flash("Client request has already been reviewed.", "info")
        return redirect(url_for("user_management.index"))

    org_id = resolve_org_id()
    tin = (client.tin or "").strip()
    if not tin or len(tin) != 10 or not tin.isdigit():
        flash("TIN must be a 10 digit number before approval.", "danger")
        return redirect(url_for("user_management.index"))

    institution = Institution.query.filter_by(org_id=org_id, tin=tin).first()
    if institution is None:
        institution = Institution(
            org_id=org_id,
            tin=tin,
            name=client.institution_name or "",
            region=client.region or "",
            zone=client.zone or "",
            city=client.city or "",
            address_line=client.address_line or "",
            phone=client.phone or "",
            email=client.email or "",
        )
        db.session.add(institution)
        db.session.flush()

    account = ClientAccount(
        org_id=org_id,
        institution_id=institution.id,
        email=client.email,
        phone=client.phone,
        full_name=client.client_name,
        position=client.position,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(UTC),
    )
    set_password(account, token_urlsafe(18))
    db.session.add(account)
    db.session.flush()

    _assign_client_role(account, "client")
    client.status = "approved"
    client.reviewed_by_id = getattr(current_user, "id", None)
    client.reviewed_at = datetime.now(UTC)

    db.session.commit()
    flash("Client approved and account created.", "success")
    return redirect(url_for("user_management.index"))


@bp.post("/clients/<int:client_id>/reject")
@require_permission("clients", "reject")
def reject_client(client_id: int):
    client = ClientRegistration.query.get_or_404(client_id)
    if client.status != "pending":
        flash("Client request has already been reviewed.", "info")
        return redirect(url_for("user_management.index"))

    client.status = "rejected"
    client.reviewed_by_id = getattr(current_user, "id", None)
    client.reviewed_at = datetime.now(UTC)
    db.session.commit()
    flash("Client rejected", "warning")
    return redirect(url_for("user_management.index"))


@bp.post("/users/<int:user_id>/delete")
@require_permission("users", "delete")
def delete_user(user_id: int):
    user = User.query.get_or_404(user_id)
    UserRoleAssignment.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash("User removed", "success")
    return redirect(url_for("user_management.index"))
