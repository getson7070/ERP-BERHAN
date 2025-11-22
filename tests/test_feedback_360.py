from datetime import date


def test_feedback_recorded(db_session, resolve_org_id):
    org_id = resolve_org_id()
    from erp.models import Feedback360, PerformanceEvaluation, ReviewCycle

    cycle = ReviewCycle(
        org_id=org_id,
        name="Test",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )
    db_session.add(cycle)
    db_session.flush()

    evaluation = PerformanceEvaluation(
        org_id=org_id,
        cycle_id=cycle.id,
        subject_type="employee",
        subject_id=1,
        total_score=80,
    )
    db_session.add(evaluation)
    db_session.flush()

    db_session.add(
        Feedback360(
            org_id=org_id,
            evaluation_id=evaluation.id,
            giver_type="user",
            giver_id=2,
            rating=4.5,
            comment="Good teamwork",
            dimension="teamwork",
        )
    )
    db_session.commit()

    assert (
        Feedback360.query.filter_by(org_id=org_id, evaluation_id=evaluation.id).count()
        == 1
    )
