"""Celery task to compute performance evaluations for a review cycle."""
from __future__ import annotations

from celery import shared_task

from erp.extensions import db
from erp.models import CRMAccount, Inventory, PerformanceEvaluation, ReviewCycle, ScorecardTemplate, User
from erp.services.performance_engine import compute_scorecard


@shared_task(name="erp.tasks.performance.compute_cycle")
def compute_cycle(org_id: int, cycle_id: int):
    cycle = ReviewCycle.query.filter_by(org_id=org_id, id=cycle_id).first()
    if not cycle:
        return {"error": "cycle_not_found"}

    templates = ScorecardTemplate.query.filter_by(org_id=org_id, is_active=True).all()
    by_type = {t.subject_type: t for t in templates if t.is_default}

    def _persist_eval(subject_type: str, subject_id: int, template: ScorecardTemplate):
        total, breakdown = compute_scorecard(
            org_id,
            template,
            subject_type,
            subject_id,
            cycle.start_date,
            cycle.end_date,
        )
        PerformanceEvaluation.query.filter_by(
            org_id=org_id,
            cycle_id=cycle.id,
            subject_type=subject_type,
            subject_id=subject_id,
        ).delete()
        db.session.add(
            PerformanceEvaluation(
                org_id=org_id,
                cycle_id=cycle.id,
                subject_type=subject_type,
                subject_id=subject_id,
                scorecard_template_id=template.id,
                total_score=total,
                breakdown_json=breakdown,
            )
        )

    emp_tpl = by_type.get("employee")
    if emp_tpl:
        user_query = User.query
        if hasattr(User, "org_id"):
            user_query = user_query.filter_by(org_id=org_id)
        user_query = user_query.filter_by(is_active=True)
        for user in user_query.all():
            _persist_eval("employee", user.id, emp_tpl)

    client_tpl = by_type.get("client")
    if client_tpl:
        client_query = CRMAccount.query
        if hasattr(CRMAccount, "org_id"):
            client_query = client_query.filter_by(org_id=org_id)
        elif hasattr(CRMAccount, "organization_id"):
            client_query = client_query.filter_by(organization_id=org_id)
        client_query = client_query.filter_by(is_active=True)
        for client in client_query.all():
            _persist_eval("client", client.id, client_tpl)

    inv_tpl = by_type.get("inventory") or by_type.get("item")
    if inv_tpl:
        inv_query = Inventory.query
        if hasattr(Inventory, "org_id"):
            inv_query = inv_query.filter_by(org_id=org_id)
        inv_query = inv_query.filter_by(**{k: True for k in ("is_active",) if hasattr(Inventory, k)})
        for item in inv_query.all():
            _persist_eval("inventory", item.id, inv_tpl)

    db.session.commit()
    return {"status": "computed"}
