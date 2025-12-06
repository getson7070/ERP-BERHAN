# erp/routes/admin.py
from __future__ import annotations

from flask import Blueprint, render_template, request, session, flash
from flask_login import login_required
from sqlalchemy import text

from db import get_db
from erp.security import require_roles, mfa_required
from erp.utils import sanitize_sort, sanitize_direction

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
    org_id = session.get("org_id") or 1  # adjust if you centralise org resolution

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
    conn.close()

    return render_template("admin/workflows.html", workflows=rows)


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


@bp.route("/bots")
@login_required
@require_roles("admin", "analytics")
@mfa_required
def bots_dashboard():
    """UI shell that talks to /api/bot-dashboard/summary and /events."""
    return render_template("admin/bots_dashboard.html")
