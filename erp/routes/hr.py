"""Human resources endpoints covering employee management."""
from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from erp.security import require_roles

from erp.extensions import db
from erp.models import Employee
from erp.utils import resolve_org_id

bp = Blueprint("hr", __name__, url_prefix="/hr")


def _serialize(employee: Employee) -> dict[str, object]:
    return {
        "id": employee.id,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": employee.email,
        "role": employee.role,
        "is_active": employee.is_active,
    }


@bp.route("/", methods=["GET", "POST"])
@require_roles("hr", "admin")
def index():
    """List employees or create a new record."""

    org_id = resolve_org_id()
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        first_name = (payload.get("first_name") or "").strip()
        last_name = (payload.get("last_name") or "").strip()
        email = (payload.get("email") or "").strip()
        role = (payload.get("role") or "staff").strip()
        if not first_name or not last_name or not email:
            return (
                jsonify({"error": "first_name, last_name and email are required"}),
                HTTPStatus.BAD_REQUEST,
            )

        employee = Employee(
            organization_id=org_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            phone=payload.get("phone"),
            is_active=payload.get("is_active", True),
        )
        db.session.add(employee)
        db.session.commit()
        return jsonify(_serialize(employee)), HTTPStatus.CREATED

    employees = Employee.tenant_query(org_id).order_by(Employee.last_name).all()
    return jsonify([_serialize(emp) for emp in employees])



