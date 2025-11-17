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
from erp.utils import login_required, resolve_org_id, role_required
from erp.models import Recruitment, PerformanceReview
from erp.extensions import db

hr_workflows_bp = Blueprint("hr_workflows", __name__, url_prefix="/hr")
# Alias for app factory imports
bp = hr_workflows_bp


@bp.route("/recruitment", methods=["GET", "POST"])
@login_required
@role_required("Manager", "Admin")
def recruitment():
    """Create and list recruitment records."""
    org_id = resolve_org_id()
    if request.method == "POST":
        candidate = request.form.get("candidate_name", "").strip()
        position = request.form.get("position", "").strip()
        email = (request.form.get("candidate_email") or "").strip()
        if not candidate or not position:
            flash("Candidate and position are required", "danger")
        elif email and "@" not in email:
            flash("Email must be valid", "danger")
        else:
            record = Recruitment(
                candidate_name=candidate,
                candidate_email=email or None,
                candidate_phone=request.form.get("candidate_phone"),
                position=position,
                source=request.form.get("source") or None,
                resume_url=request.form.get("resume_url") or None,
                stage=request.form.get("stage") or "screening",
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
@role_required("Manager", "Admin")
def performance():
    """Capture and list performance reviews."""
    org_id = resolve_org_id()
    if request.method == "POST":
        employee = request.form.get("employee_name", "").strip()
        score_raw = request.form.get("score", "").strip()
        try:
            score = float(score_raw)
        except ValueError:
            score = -1
        if not employee or score < 0 or score > 5:
            flash("Valid employee and score (0-5) required", "danger")
        else:
            review = PerformanceReview(
                organization_id=org_id,
                employee_name=employee,
                score=score,
                goals=request.form.get("goals"),
                competencies=request.form.get("competencies"),
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


@bp.post("/performance/<int:review_id>/finalize")
@login_required
@role_required("Manager", "Admin")
def finalize_review(review_id: int):
    org_id = resolve_org_id()
    review = PerformanceReview.query.filter_by(
        id=review_id, organization_id=org_id
    ).first_or_404()
    review.finalize()
    db.session.commit()
    flash("Review finalized", "success")
    return redirect(url_for("hr_workflows.performance"))



