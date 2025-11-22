"""Heuristic ML suggestion scaffold pending full model integration."""
from __future__ import annotations

from celery import shared_task

from erp.extensions import db
from erp.models import MLSuggestion, PerformanceEvaluation


@shared_task(name="erp.tasks.ml.make_suggestions")
def make_suggestions(org_id: int, cycle_id: int):
    evals = PerformanceEvaluation.query.filter_by(org_id=org_id, cycle_id=cycle_id).all()

    for evaluation in evals:
        score = float(evaluation.total_score)

        if evaluation.subject_type == "employee":
            if score < 60:
                db.session.add(
                    MLSuggestion(
                        org_id=org_id,
                        cycle_id=cycle_id,
                        subject_type="employee",
                        subject_id=evaluation.subject_id,
                        suggestion_type="training_needed",
                        confidence=0.72,
                        reason_json={"score": score, "threshold": 60},
                    )
                )
            if score > 90:
                db.session.add(
                    MLSuggestion(
                        org_id=org_id,
                        cycle_id=cycle_id,
                        subject_type="employee",
                        subject_id=evaluation.subject_id,
                        suggestion_type="promotion_candidate",
                        confidence=0.65,
                        reason_json={"score": score},
                    )
                )

        if evaluation.subject_type == "client" and score < 55:
            db.session.add(
                MLSuggestion(
                    org_id=org_id,
                    cycle_id=cycle_id,
                    subject_type="client",
                    subject_id=evaluation.subject_id,
                    suggestion_type="churn_risk",
                    confidence=0.68,
                    reason_json={"score": score, "threshold": 55},
                )
            )

    db.session.commit()
    return {"status": "ok"}
