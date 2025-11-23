"""Policy management endpoints for Phase-2 RBAC."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.models import RBACPolicy, RBACPolicyRule
from erp.security import require_roles
from erp.security_rbac_phase2 import invalidate_policy_cache
from erp.utils import resolve_org_id

bp = Blueprint("rbac_policy_api", __name__, url_prefix="/api/rbac/policies")


def _serialize_policy(policy: RBACPolicy) -> dict:
    return {
        "id": policy.id,
        "name": policy.name,
        "description": policy.description,
        "priority": policy.priority,
        "is_active": policy.is_active,
        "rules": [
            {
                "id": r.id,
                "role_key": r.role_key,
                "resource": r.resource,
                "action": r.action,
                "effect": r.effect,
                "conditions": r.condition_json,
            }
            for r in policy.rules
        ],
    }


@bp.get("")
@require_roles("admin", "superadmin")
def list_policies():
    org_id = resolve_org_id()
    rows = (
        RBACPolicy.query.filter_by(org_id=org_id)
        .order_by(RBACPolicy.priority.asc())
        .all()
    )
    return jsonify([_serialize_policy(p) for p in rows]), HTTPStatus.OK


@bp.post("")
@require_roles("admin", "superadmin")
def create_policy():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    if not payload.get("name"):
        return jsonify({"error": "name_required"}), HTTPStatus.BAD_REQUEST

    policy = RBACPolicy(
        org_id=org_id,
        name=payload["name"],
        description=payload.get("description"),
        priority=int(payload.get("priority", 100)),
        is_active=bool(payload.get("is_active", True)),
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(policy)
    db.session.flush()

    for rule in payload.get("rules", []):
        db.session.add(
            RBACPolicyRule(
                org_id=org_id,
                policy_id=policy.id,
                role_key=rule["role_key"],
                resource=rule["resource"],
                action=rule["action"],
                effect=rule.get("effect", "allow"),
                condition_json=rule.get("conditions", {}),
            )
        )

    db.session.commit()
    invalidate_policy_cache()
    return jsonify({"id": policy.id}), HTTPStatus.CREATED


@bp.put("/<int:policy_id>")
@require_roles("admin", "superadmin")
def update_policy(policy_id: int):
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    policy = RBACPolicy.query.filter_by(org_id=org_id, id=policy_id).first_or_404()
    policy.description = payload.get("description", policy.description)
    policy.priority = int(payload.get("priority", policy.priority))
    policy.is_active = bool(payload.get("is_active", policy.is_active))

    RBACPolicyRule.query.filter_by(org_id=org_id, policy_id=policy.id).delete()
    for rule in payload.get("rules", []):
        db.session.add(
            RBACPolicyRule(
                org_id=org_id,
                policy_id=policy.id,
                role_key=rule["role_key"],
                resource=rule["resource"],
                action=rule["action"],
                effect=rule.get("effect", "allow"),
                condition_json=rule.get("conditions", {}),
            )
        )

    db.session.commit()
    invalidate_policy_cache()
    return jsonify({"status": "updated"}), HTTPStatus.OK


@bp.delete("/<int:policy_id>")
@require_roles("superadmin")
def delete_policy(policy_id: int):
    org_id = resolve_org_id()
    RBACPolicy.query.filter_by(org_id=org_id, id=policy_id).delete()
    db.session.commit()
    invalidate_policy_cache()
    return jsonify({"status": "deleted"}), HTTPStatus.OK


__all__ = ["bp"]
