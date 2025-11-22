"""Human resources endpoints covering employee lifecycle, reviews and leave."""

from __future__ import annotations

from datetime import date, datetime
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.security import require_roles, require_login
from erp.extensions import db
from erp.models import (
    Employee,
    HROnboarding,
    HROffboarding,
    PerformanceReview,
    LeaveRequest,
)
from erp.utils import resolve_org_id

bp = Blueprint("hr", __name__, url_prefix="/hr")


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def _serialize_employee(employee: Employee) -> dict[str, Any]:
    return {
        "id": employee.id,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": employee.email,
        "role": employee.role,
        "is_active": employee.is_active,
        "phone": getattr(employee, "phone", None),
    }


def _serialize_onboarding(rec: HROnboarding) -> dict[str, Any]:
    return {
        "id": rec.id,
        "employee_id": rec.employee_id,
        "organization_id": rec.organization_id,
        "start_date": rec.start_date.isoformat(),
        "contract_type": rec.contract_type,
        "checklist": rec.checklist_json or {},
        "completed": rec.completed,
        "notes": rec.notes,
        "created_at": rec.created_at.isoformat(),
    }


def _serialize_offboarding(rec: HROffboarding) -> dict[str, Any]:
    return {
        "id": rec.id,
        "employee_id": rec.employee_id,
        "organization_id": rec.organization_id,
        "last_working_day": rec.last_working_day.isoformat(),
        "reason": rec.reason,
        "checklist": rec.checklist_json or {},
        "completed": rec.completed,
        "notes": rec.notes,
        "created_at": rec.created_at.isoformat(),
    }


def _serialize_review(review: PerformanceReview) -> dict[str, Any]:
    return {
        "id": review.id,
        "employee_id": review.employee_id,
        "organization_id": review.organization_id,
        "period_start": review.period_start.isoformat(),
        "period_end": review.period_end.isoformat(),
        "score": review.score,
        "rating": review.rating,
        "summary": review.summary,
        "reviewer_id": review.reviewer_id,
        "created_at": review.created_at.isoformat(),
        "updated_at": review.updated_at.isoformat(),
    }


def _serialize_leave(req: LeaveRequest) -> dict[str, Any]:
    return {
        "id": req.id,
        "employee_id": req.employee_id,
        "organization_id": req.organization_id,
        "start_date": req.start_date.isoformat(),
        "end_date": req.end_date.isoformat(),
        "leave_type": req.leave_type,
        "reason": req.reason,
        "status": req.status,
        "approver_id": req.approver_id,
        "decided_at": req.decided_at.isoformat() if req.decided_at else None,
        "created_at": req.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Employee CRUD
# ---------------------------------------------------------------------------

@bp.route("/employees", methods=["GET", "POST"])
@require_roles("hr", "admin")
def employees_index():
    """List employees or create a new record."""

    organization_id = resolve_org_id()

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
            organization_id=organization_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            phone=payload.get("phone"),
            is_active=payload.get("is_active", True),
        )
        db.session.add(employee)
        db.session.commit()
        return jsonify(_serialize_employee(employee)), HTTPStatus.CREATED

    employees = (
        Employee.tenant_query(organization_id)
        .order_by(Employee.last_name)
        .all()
    )
    return jsonify([_serialize_employee(emp) for emp in employees])


@bp.route("/employees/<int:employee_id>", methods=["GET", "PATCH", "DELETE"])
@require_roles("hr", "admin")
def employee_detail(employee_id: int):
    """Retrieve, update, or deactivate an employee."""
    organization_id = resolve_org_id()
    employee = Employee.tenant_query(organization_id).get_or_404(employee_id)

    if request.method == "GET":
        return jsonify(_serialize_employee(employee))

    if request.method == "PATCH":
        payload = request.get_json(silent=True) or {}
        for field in ("first_name", "last_name", "email", "role", "phone"):
            if field in payload and payload[field] is not None:
                setattr(employee, field, payload[field])
        if "is_active" in payload:
            employee.is_active = bool(payload["is_active"])
        db.session.commit()
        return jsonify(_serialize_employee(employee))

    # DELETE => soft offboarding (set inactive)
    employee.is_active = False
    db.session.commit()
    return "", HTTPStatus.NO_CONTENT


# ---------------------------------------------------------------------------
# Onboarding / Offboarding
# ---------------------------------------------------------------------------

@bp.post("/employees/<int:employee_id>/onboarding")
@require_roles("hr", "admin")
def create_or_update_onboarding(employee_id: int):
    """Create or update onboarding record for an employee."""
    organization_id = resolve_org_id()
    Employee.tenant_query(organization_id).get_or_404(employee_id)

    payload = request.get_json(silent=True) or {}
    start_date_raw = payload.get("start_date")
    contract_type = (payload.get("contract_type") or "permanent").lower()
    if not start_date_raw:
        return jsonify({"error": "start_date is required"}), HTTPStatus.BAD_REQUEST

    start_date = date.fromisoformat(start_date_raw)

    record = HROnboarding.query.filter_by(
        organization_id=organization_id, employee_id=employee_id
    ).one_or_none()

    if record is None:
        record = HROnboarding(
            organization_id=organization_id,
            employee_id=employee_id,
            start_date=start_date,
            contract_type=contract_type,
            checklist_json=payload.get("checklist") or {},
            completed=bool(payload.get("completed", False)),
            notes=payload.get("notes"),
            created_by_id=getattr(current_user, "id", None),
        )
        db.session.add(record)
    else:
        record.start_date = start_date
        record.contract_type = contract_type
        record.checklist_json = payload.get("checklist") or record.checklist_json
        if "completed" in payload:
            record.completed = bool(payload["completed"])
        if "notes" in payload:
            record.notes = payload["notes"]

    db.session.commit()
    return jsonify(_serialize_onboarding(record)), HTTPStatus.OK


@bp.get("/employees/<int:employee_id>/onboarding")
@require_roles("hr", "admin")
def get_onboarding(employee_id: int):
    organization_id = resolve_org_id()
    Employee.tenant_query(organization_id).get_or_404(employee_id)

    record = HROnboarding.query.filter_by(
        organization_id=organization_id, employee_id=employee_id
    ).one_or_none()
    if record is None:
        return jsonify({"onboarding": None}), HTTPStatus.OK
    return jsonify(_serialize_onboarding(record)), HTTPStatus.OK


@bp.post("/employees/<int:employee_id>/offboarding")
@require_roles("hr", "admin")
def create_offboarding(employee_id: int):
    """Create offboarding record (off-boarding is usually one-shot)."""
    organization_id = resolve_org_id()
    employee = Employee.tenant_query(organization_id).get_or_404(employee_id)

    payload = request.get_json(silent=True) or {}
    last_day_raw = payload.get("last_working_day")
    reason = (payload.get("reason") or "").strip()

    if not last_day_raw or not reason:
        return (
            jsonify({"error": "last_working_day and reason are required"}),
            HTTPStatus.BAD_REQUEST,
        )

    last_day = date.fromisoformat(last_day_raw)

    record = HROffboarding(
        organization_id=organization_id,
        employee_id=employee_id,
        last_working_day=last_day,
        reason=reason,
        checklist_json=payload.get("checklist") or {},
        completed=bool(payload.get("completed", False)),
        notes=payload.get("notes"),
        created_by_id=getattr(current_user, "id", None),
    )
    employee.is_active = False  # soft terminate
    db.session.add(record)
    db.session.commit()
    return jsonify(_serialize_offboarding(record)), HTTPStatus.CREATED


@bp.get("/employees/<int:employee_id>/offboarding")
@require_roles("hr", "admin")
def get_offboarding(employee_id: int):
    organization_id = resolve_org_id()
    Employee.tenant_query(organization_id).get_or_404(employee_id)
    record = (
        HROffboarding.query.filter_by(organization_id=organization_id, employee_id=employee_id)
        .order_by(HROffboarding.created_at.desc())
        .first()
    )
    if record is None:
        return jsonify({"offboarding": None}), HTTPStatus.OK
    return jsonify(_serialize_offboarding(record)), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Performance reviews
# ---------------------------------------------------------------------------

@bp.get("/employees/<int:employee_id>/reviews")
@require_roles("hr", "admin")
def list_reviews(employee_id: int):
    organization_id = resolve_org_id()
    Employee.tenant_query(organization_id).get_or_404(employee_id)
    reviews = (
        PerformanceReview.query.filter_by(organization_id=organization_id, employee_id=employee_id)
        .order_by(PerformanceReview.period_end.desc())
        .all()
    )
    return jsonify([_serialize_review(r) for r in reviews]), HTTPStatus.OK


@bp.post("/employees/<int:employee_id>/reviews")
@require_roles("hr", "admin")
def create_review(employee_id: int):
    organization_id = resolve_org_id()
    Employee.tenant_query(organization_id).get_or_404(employee_id)

    payload = request.get_json(silent=True) or {}
    start_raw = payload.get("period_start")
    end_raw = payload.get("period_end")
    score = payload.get("score")

    if not start_raw or not end_raw or score is None:
        return (
            jsonify({"error": "period_start, period_end and score are required"}),
            HTTPStatus.BAD_REQUEST,
        )

    review = PerformanceReview(
        organization_id=organization_id,
        employee_id=employee_id,
        period_start=date.fromisoformat(start_raw),
        period_end=date.fromisoformat(end_raw),
        score=int(score),
        rating=payload.get("rating"),
        summary=payload.get("summary"),
        reviewer_id=getattr(current_user, "id", None),
    )
    db.session.add(review)
    db.session.commit()
    return jsonify(_serialize_review(review)), HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# Leave management
# ---------------------------------------------------------------------------

@bp.get("/employees/<int:employee_id>/leave")
@require_login
def list_leave(employee_id: int):
    """List leave requests for an employee.

    Employees can see their own leave; HR/Admin can see any employee.
    """
    organization_id = resolve_org_id()
    employee = Employee.tenant_query(organization_id).get_or_404(employee_id)

    # Simple rule: if current user is not HR/admin and not the employee => deny.
    roles = getattr(current_user, "roles", []) or []
    if (
        employee.id != getattr(current_user, "employee_id", None)
        and "hr" not in roles
        and "admin" not in roles
    ):
        return jsonify({"error": "forbidden"}), HTTPStatus.FORBIDDEN

    q = LeaveRequest.query.filter_by(organization_id=organization_id, employee_id=employee_id).order_by(
        LeaveRequest.created_at.desc()
    )
    return jsonify([_serialize_leave(lr) for lr in q.all()]), HTTPStatus.OK


@bp.post("/employees/<int:employee_id>/leave")
@require_login
def create_leave(employee_id: int):
    """Employees create leave; HR/Admin may also create on behalf of."""
    organization_id = resolve_org_id()
    employee = Employee.tenant_query(organization_id).get_or_404(employee_id)

    roles = getattr(current_user, "roles", []) or []
    # Non HR/admin can only create for self
    if (
        employee.id != getattr(current_user, "employee_id", None)
        and "hr" not in roles
        and "admin" not in roles
    ):
        return jsonify({"error": "forbidden"}), HTTPStatus.FORBIDDEN

    payload = request.get_json(silent=True) or {}
    start_raw = payload.get("start_date")
    end_raw = payload.get("end_date")
    leave_type = (payload.get("leave_type") or "").lower()

    if not start_raw or not end_raw or not leave_type:
        return (
            jsonify({"error": "start_date, end_date and leave_type are required"}),
            HTTPStatus.BAD_REQUEST,
        )

    start_date = date.fromisoformat(start_raw)
    end_date = date.fromisoformat(end_raw)
    if end_date < start_date:
        return (
            jsonify({"error": "end_date cannot be before start_date"}),
            HTTPStatus.BAD_REQUEST,
        )

    req_obj = LeaveRequest(
        organization_id=organization_id,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        leave_type=leave_type,
        reason=payload.get("reason"),
        status="pending",
    )
    db.session.add(req_obj)
    db.session.commit()
    return jsonify(_serialize_leave(req_obj)), HTTPStatus.CREATED


@bp.post("/leave/<int:leave_id>/decision")
@require_roles("hr", "admin")
def decide_leave(leave_id: int):
    """HR/Admin approve or reject leave requests."""
    organization_id = resolve_org_id()
    lr = LeaveRequest.query.filter_by(organization_id=organization_id, id=leave_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    decision = (payload.get("decision") or "").lower()
    if decision not in {"approved", "rejected"}:
        return jsonify({"error": "decision must be 'approved' or 'rejected'"}), HTTPStatus.BAD_REQUEST

    lr.status = decision
    lr.approver_id = getattr(current_user, "id", None)
    lr.decided_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize_leave(lr)), HTTPStatus.OK
