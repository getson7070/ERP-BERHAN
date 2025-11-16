"""Module: routes/hr_workflows.py — audit-added docstring. Refine with precise purpose when convenient."""
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from erp.utils import login_required, resolve_org_id
from erp.models import Recruitment, PerformanceReview
from erp.extensions import db

hr_workflows_bp = Blueprint("hr_workflows", __name__, url_prefix="/hr")
# Alias for app factory imports
bp = hr_workflows_bp


@bp.route("/recruitment", methods=["GET", "POST"])
@login_required
def recruitment():
    """Create and list recruitment records."""
    org_id = resolve_org_id()
    if request.method == "POST":
        candidate = request.form.get("candidate_name", "").strip()
        position = request.form.get("position", "").strip()
        if not candidate or not position:
            flash("Candidate and position are required", "danger")
        else:
            record = Recruitment(
                candidate_name=candidate,
                position=position,
                organization_id=org_id,
            )
            db.session.add(record)
            db.session.commit()
            flash("Recruitment record saved", "success")
            return redirect(url_for("hr_workflows.recruitment"))

    session["org_id"] = org_id
    records = (
        Recruitment.tenant_query(org_id)
        .order_by(Recruitment.applied_on.desc())
        .all()
    )
    return render_template("hr/recruitment.html", records=records)


@bp.route("/performance", methods=["GET", "POST"])
@login_required
def performance():
    """Capture and list performance reviews."""
    org_id = resolve_org_id()
    if request.method == "POST":
        employee = request.form.get("employee_name", "").strip()
        score = request.form.get("score", "").strip()
        if not employee or not score.isdigit():
            flash("Valid employee and score required", "danger")
        else:
            review = PerformanceReview(
                organization_id=org_id,
                employee_name=employee,
                score=float(score),
            )
            db.session.add(review)
            db.session.commit()
            flash("Performance review saved", "success")
            return redirect(url_for("hr_workflows.performance"))

    reviews = (
        PerformanceReview.tenant_query(org_id)
        .order_by(PerformanceReview.review_date.desc())
        .all()
    )
    return render_template("hr/performance.html", reviews=reviews)



