# erp/routes/admin.py
from __future__ import annotations

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session,
    flash,
    redirect,
    url_for,
)
from http import HTTPStatus
from flask_login import login_required
from sqlalchemy import Boolean, Column, Integer, MetaData, Table, Text as SAText, text
from sqlalchemy.exc import SQLAlchemyError

from db import get_db
from erp.health import health_registry
from erp.security import require_roles, mfa_required
from erp.security_rbac_phase2 import invalidate_policy_cache
from erp.utils import resolve_org_id, sanitize_sort, sanitize_direction
from erp.extensions import db
from erp.models import RBACPolicy, RBACPolicyRule

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/workflows", methods=["GET", "POST"])
@login_required
@require_roles("admin")
@mfa_required
def workflows():
    """Basic admin workflows page.

    This implementation is intentionally conservative:
    - Reads workflows for the current org_id from the DB.
    - Allows creating a simple workflow definition via POST.
    - Uses sanitize_sort / sanitize_direction to avoid injection.
    """

    conn = get_db()
    org_id = resolve_org_id()

    _ensure_workflows_table(conn)

    if request.method == "POST":
        form = request.form
        module = (form.get("module") or "").strip()
        steps = (form.get("steps") or "").strip()
        enabled = form.get("enabled") in ("1", "true", "on")

        if not module or not steps:
            flash("Module and steps are required.", "error")
        else:
            conn.execute(
                text(
                    """
                    INSERT INTO workflows (org_id, module, steps, enabled)
                    VALUES (:org_id, :module, :steps, :enabled)
                    """
                ),
                {
                    "org_id": org_id,
                    "module": module,
                    "steps": steps,
                    "enabled": enabled,
                },
            )
            conn.commit()
            flash("Workflow saved.", "success")

    sort = sanitize_sort(
        request.args.get("sort"),
        allowed=["module", "id", "enabled"],
        default="module",
    )
    direction = sanitize_direction(request.args.get("direction"), default="asc")
    order_clause = f"{sort} {direction}"

    try:
        rows = conn.execute(
            text(
                f"""
                SELECT id, module, steps, enabled, org_id
                FROM workflows
                WHERE org_id = :org_id
                ORDER BY {order_clause}
                """
            ),
            {"org_id": org_id},
        ).fetchall()
    finally:
        conn.close()

    return render_template("admin/workflows.html", workflows=rows)


def _ensure_workflows_table(conn) -> None:
    """Create the workflows table when missing to avoid 500s on fresh tenants."""

    metadata = MetaData()
    workflows = Table(
        "workflows",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("org_id", Integer, nullable=False, index=True),
        Column("module", SAText, nullable=False),
        Column("steps", SAText, nullable=False),
        Column("enabled", Boolean, nullable=False, default=True),
    )
    try:
        metadata.create_all(bind=conn, tables=[workflows])
    except SQLAlchemyError:
        conn.rollback()
        raise


@bp.route("/panel")
@login_required
@require_roles("admin")
@mfa_required
def panel():
    """Admin landing page with links to workflows, audit logs, and bot dashboard."""
    return render_template("admin/panel.html")


@bp.route("/audit/logs")
@login_required
@require_roles("admin", "compliance", "audit")
@mfa_required
def audit_logs():
    """UI shell that talks to /api/audit/logs and /api/audit/export."""
    return render_template("admin/audit_logs.html")


@bp.route("/rbac", methods=["GET", "POST"])
@login_required
@require_roles("admin", "management", "supervisor")
@mfa_required
def rbac_console():
    """Minimal UI to inspect and edit RBAC policies safely."""

    org_id = resolve_org_id()
    policies = (
        RBACPolicy.query.filter_by(org_id=org_id)
        .order_by(RBACPolicy.priority.asc())
        .all()
    )

    if request.method == "POST":
        policy_id = request.form.get("policy_id")
        role_key = (request.form.get("role_key") or "").strip().lower()
        resource = (request.form.get("resource") or "").strip()
        action = (request.form.get("action") or "").strip()
        effect = (request.form.get("effect") or "allow").strip().lower()

        if effect not in {"allow", "deny"}:
            flash("Effect must be allow or deny.", "danger")
            return redirect(url_for("admin.rbac_console"))

        if not (role_key and resource and action):
            flash("Role, resource, and action are required.", "danger")
            return redirect(url_for("admin.rbac_console"))

        target_policy = None
        if policy_id:
            target_policy = RBACPolicy.query.filter_by(
                org_id=org_id, id=int(policy_id)
            ).first()
        if target_policy is None:
            target_policy = RBACPolicy(
                org_id=org_id,
                name="Custom policy",
                description="Ad-hoc rules from admin console",
                priority=90,
                is_active=True,
            )
            db.session.add(target_policy)
            db.session.flush()

        db.session.add(
            RBACPolicyRule(
                org_id=org_id,
                policy_id=target_policy.id,
                role_key=role_key,
                resource=resource,
                action=action,
                effect=effect,
            )
        )
        db.session.commit()
        invalidate_policy_cache()
        flash("RBAC rule saved.", "success")
        return redirect(url_for("admin.rbac_console"))

    return render_template("admin/rbac.html", policies=policies)


@bp.route("/bots")
@login_required
@require_roles("admin", "analytics")
@mfa_required
def bots_dashboard():
    """UI shell that talks to /api/bot-dashboard/summary and /events."""
    return render_template("admin/bots_dashboard.html")


@bp.route("/analytics/operations")
@login_required
@require_roles("admin", "analytics", "management", "supervisor")
@mfa_required
def operations_analytics():
    """Dashboard for maintenance escalations and geo offline alerts."""

    return render_template("admin/ops_analytics.html")


@bp.route("/health", methods=["GET"])
@login_required
@require_roles("admin", "management", "supervisor", "compliance")
@mfa_required
def health_dashboard():
    """Privileged, MFA-gated health dashboard with JSON/HTML views.

    - Surfaces registry-backed health checks (config, migration drift, DB, redis, etc.).
    - Uses JSON when explicitly requested (Accept: application/json or format=json).
    - Applies secure defaults by requiring admin/management/supervisor/compliance roles.
    """

    overall_ok, results = health_registry.run_all()

    payload = {
        "status": "ok" if overall_ok else "error",
        "ok": overall_ok,
        "checks": results,
    }

    prefers_json = request.args.get("format") == "json"
    if not prefers_json:
        prefers_json = (
            request.accept_mimetypes.accept_json
            and not request.accept_mimetypes.accept_html
        )

    if prefers_json:
        status_code = HTTPStatus.OK if overall_ok else HTTPStatus.SERVICE_UNAVAILABLE
        return jsonify(payload), status_code

    # Compute quick aggregates for the UI chips.
    critical_total = sum(1 for meta in results.values() if meta.get("critical"))
    critical_failed = sum(
        1 for meta in results.values() if meta.get("critical") and not meta.get("ok")
    )
    non_critical_failed = sum(
        1 for meta in results.values() if not meta.get("critical") and not meta.get("ok")
    )

    return render_template(
        "admin/health_dashboard.html",
        ok=overall_ok,
        results=results,
        payload=payload,
        critical_total=critical_total,
        critical_failed=critical_failed,
        non_critical_failed=non_critical_failed,
    )
