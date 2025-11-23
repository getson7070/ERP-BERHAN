"""Phase-2 RBAC models for policy-driven permissions.

These tables enable dynamic policy management, deny-overrides, role
hierarchies, and role-assignment workflows. They intentionally avoid
business logic so the evaluation engine can remain separate and easily
cached.
"""

from __future__ import annotations

from sqlalchemy import UniqueConstraint, func

from erp.extensions import db


class RBACPolicy(db.Model):
    __tablename__ = "rbac_policies"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    name = db.Column(db.String(128), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    priority = db.Column(db.Integer, nullable=False, default=100, index=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id = db.Column(db.Integer, nullable=True)

    rules = db.relationship(
        "RBACPolicyRule",
        back_populates="policy",
        cascade="all, delete-orphan",
        order_by="RBACPolicyRule.id",
    )

    __table_args__ = (
        UniqueConstraint("org_id", "name", name="uq_policy_name"),
    )


class RBACPolicyRule(db.Model):
    __tablename__ = "rbac_policy_rules"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    policy_id = db.Column(
        db.Integer,
        db.ForeignKey("rbac_policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role_key = db.Column(db.String(64), nullable=False, index=True)
    resource = db.Column(db.String(128), nullable=False, index=True)
    action = db.Column(db.String(64), nullable=False, index=True)

    effect = db.Column(db.String(8), nullable=False, default="allow")
    condition_json = db.Column(db.JSON, nullable=False, default=dict)

    policy = db.relationship("RBACPolicy", back_populates="rules")

    __table_args__ = (
        db.Index("ix_policy_role_res_act", "org_id", "role_key", "resource", "action"),
    )


class RoleHierarchy(db.Model):
    """Defines role dominance for safe delegation."""

    __tablename__ = "role_hierarchy"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    parent_role = db.Column(db.String(64), nullable=False, index=True)
    child_role = db.Column(db.String(64), nullable=False, index=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("org_id", "parent_role", "child_role", name="uq_role_hierarchy"),
    )


class RoleAssignmentRequest(db.Model):
    """Tracks requests for dynamic role assignments with approvals."""

    __tablename__ = "role_assignment_requests"

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    requester_id = db.Column(db.Integer, nullable=False, index=True)
    target_user_id = db.Column(db.Integer, nullable=False, index=True)

    role_key = db.Column(db.String(64), nullable=False, index=True)
    reason = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(32), nullable=False, default="pending", index=True)
    reviewed_by_id = db.Column(db.Integer, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        db.Index("ix_role_req_org_status", "org_id", "status"),
    )


__all__ = [
    "RBACPolicy",
    "RBACPolicyRule",
    "RoleHierarchy",
    "RoleAssignmentRequest",
]
