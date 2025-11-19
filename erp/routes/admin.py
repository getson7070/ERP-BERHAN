# erp/routes/admin.py
from __future__ import annotations

from flask import Blueprint, render_template, request, session, flash
from sqlalchemy import text

from db import get_db
from erp.security import require_roles, mfa_required
from erp.utils import sanitize_sort, sanitize_direction
sanitize_direction

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/workflows", methods=["GET", "POST"])
@require_roles("admin")
@mfa_required
def workflows():
    """
    Manage per-org workflows using parameterised SQL.

    Existing body of this function stays exactly as it is below.
    """
    # keep your existing function body here...

    Still uses raw SQL (no ORM model yet) but strictly with bound parameters,
    plus basic validation on user input.
    """
    org_id = session.get("org_id")
    if not org_id:
        flash("Missing organisation context.", "danger")
        return render_template("admin/workflows.html", workflows=[])

    conn = get_db()

    if request.method == "POST":
        module = (request.form.get("module") or "").strip()
        steps = (request.form.get("steps") or "").strip()
        enabled = request.form.get("enabled") == "on"

        # Basic validation – adjust as you like
        if not module:
            flash("Module is required.", "danger")
        elif len(module) > 64:
            flash("Module name is too long.", "danger")
        else:
            conn.execute(
                text(
                    """
                    INSERT INTO workflows (org_id, module, steps, enabled)
                    VALUES (:org, :module, :steps, :enabled)
                    """
                ),
                {"org": org_id, "module": module, "steps": steps, "enabled": enabled},
            )
            conn.commit()
            flash("Workflow saved.", "success")

    # safe sort direction / column if you add query params later
    sort = sanitize_sort(request.args.get("sort"), allowed=["module", "id", "enabled"], default="module")
    direction = sanitize_direction(request.args.get("direction"), default="asc")

    wf = conn.execute(
        text(
            f"""
            SELECT id, module, steps, enabled
            FROM workflows
            WHERE org_id = :org
            ORDER BY {sort} {direction}
            """
        ),
        {"org": org_id},
    ).fetchall()
    conn.close()
    return render_template("admin/workflows.html", workflows=wf)


@bp.route("/panel")
@login_required
@mfa_required
def panel():
    """Simple administrative panel protected by MFA."""
    return "admin panel"
