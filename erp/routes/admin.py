from flask import Blueprint, render_template, request, session
from db import get_db
from erp.utils import login_required, mfa_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/workflows", methods=["GET", "POST"])
def workflows():
    org_id = session.get("org_id")
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        module = request.form["module"]
        steps = request.form["steps"]
        enabled = request.form.get("enabled") == "on"
        cur.execute(
            (
                "INSERT INTO workflows (org_id, module, steps, enabled) "
                "VALUES (%s,%s,%s,%s)"
            ),
            (org_id, module, steps, enabled),
        )
        conn.commit()
    cur.execute(
        (
            "SELECT id, module, steps, enabled FROM workflows "
            "WHERE org_id = %s ORDER BY module"
        ),
        (org_id,),
    )
    wf = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin/workflows.html", workflows=wf)


@bp.route('/panel')
@login_required
@mfa_required
def panel():
    """Simple administrative panel protected by MFA."""
    return 'admin panel'
