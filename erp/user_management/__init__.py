"""User management blueprint powering the admin console."""
from __future__ import annotations

from datetime import UTC, datetime
from secrets import token_urlsafe

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from erp.security import require_roles
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
@require_roles("admin")
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
            user = User(username=username, email=email)
            user.password = password  # hashed via setter
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
    users = (
        db.session.query(User, Role.name)
        .join(UserRoleAssignment, UserRoleAssignment.user_id == User.id, isouter=True)
        .join(Role, Role.id == UserRoleAssignment.role_id, isouter=True)
        .order_by(User.username)
        .all()
    )
    users_list = [
        {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "role": role or "--",
        }
        for user, role in users
    ]
    return render_template(
        "user_management/index.html",
        pending_clients=pending_clients,
        users_list=users_list,
    )


@bp.post("/clients/<int:client_id>/approve")
@require_roles("admin", "manager")
def approve_client(client_id: int):
    client = ClientRegistration.query.get_or_404(client_id)
    if client.status != "pending":
        flash("Client request has already been reviewed.", "info")
        return redirect(url_for("user_management.index"))

    org_id = resolve_org_id()
    institution = Institution.query.filter_by(org_id=org_id, tin=client.tin).first()
    if institution is None:
        institution = Institution(
            org_id=org_id,
            tin=client.tin,
            legal_name=client.institution_name,
            region=client.region,
            zone=client.zone,
            city=client.city,
            subcity=client.subcity,
            woreda=client.woreda,
            kebele=client.kebele,
            street=client.street,
            house_number=client.house_number,
            gps_hint=client.gps_hint,
            main_phone=client.phone,
            main_email=client.email,
        )
        db.session.add(institution)
        db.session.flush()

    account = ClientAccount.query.filter_by(org_id=org_id, email=client.email).first()
    if account is None:
        account = ClientAccount(
            org_id=org_id,
            client_id=institution.id,
            institution_id=institution.id,
            email=client.email,
            phone=client.phone,
            is_active=True,
            is_verified=True,
        )
        if client.password_hash:
            account.password_hash = client.password_hash
        else:
            set_password(account, token_urlsafe(16))
        db.session.add(account)
        db.session.flush()
        _assign_client_role(account, "client")

    client.status = "approved"
    client.decided_at = datetime.now(UTC)
    client.decided_by = getattr(current_user, "id", None)
    client.decision_notes = request.form.get("decision_notes") or client.decision_notes
    db.session.commit()
    flash("Client approved and account provisioned", "success")
    return redirect(url_for("user_management.index"))


@bp.post("/clients/<int:client_id>/reject")
@require_roles("admin", "manager")
def reject_client(client_id: int):
    client = ClientRegistration.query.get_or_404(client_id)
    client.status = "rejected"
    client.decided_at = datetime.now(UTC)
    client.decided_by = getattr(current_user, "id", None)
    db.session.commit()
    flash("Client rejected", "warning")
    return redirect(url_for("user_management.index"))


@bp.post("/users/<int:user_id>/delete")
@require_roles("admin")
def delete_user(user_id: int):
    user = User.query.get_or_404(user_id)
    UserRoleAssignment.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash("User removed", "success")
    return redirect(url_for("user_management.index"))
