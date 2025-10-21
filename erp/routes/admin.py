﻿from flask import Blueprint, render_template, request, session
from sqlalchemy import text
from db import get_db
from erp.utils import login_required, mfa_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/workflows", methods=["GET", "POST"])
def workflows():
    org_id = session.get("org_id")
    conn = get_db()
    if request.method == "POST":
        module = request.form["module"]
        steps = request.form["steps"]
        enabled = request.form.get("enabled") == "on"
        conn.execute(
            text(
                "INSERT INTO workflows (org_id, module, steps, enabled) VALUES (:org,:module,:steps,:enabled)"
            ),
            {"org": org_id, "module": module, "steps": steps, "enabled": enabled},
        )
        conn.commit()
    wf = conn.execute(
        text(
            "SELECT id, module, steps, enabled FROM workflows WHERE org_id = :org ORDER BY module"
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


