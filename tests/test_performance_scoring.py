from datetime import date
from decimal import Decimal


def test_scorecard_computation_simple(db_session, resolve_org_id):
    org_id = resolve_org_id()
    from erp.models import AnalyticsFact, KPIRegistry, ScorecardItem, ScorecardTemplate
    from erp.services.performance_engine import compute_scorecard

    db_session.add(
        KPIRegistry(
            org_id=org_id,
            kpi_key="sales.monthly_revenue",
            name="Revenue",
            target_value=Decimal("100"),
            weight=1.0,
            direction="higher_better",
        )
    )
    tpl = ScorecardTemplate(
        org_id=org_id, name="Sales Rep", subject_type="employee", is_default=True
    )
    db_session.add(tpl)
    db_session.flush()
    db_session.add(
        ScorecardItem(
            org_id=org_id, template_id=tpl.id, kpi_key="sales.monthly_revenue"
        )
    )

    for offset in range(5):
        db_session.add(
            AnalyticsFact(
                org_id=org_id,
                metric_key="sales.monthly_revenue",
                ts_date=date(2025, 1, 1 + offset),
                user_id=7,
                value=Decimal("100"),
            )
        )
    db_session.commit()

    total, breakdown = compute_scorecard(
        org_id, tpl, "employee", 7, date(2025, 1, 1), date(2025, 1, 31)
    )
    assert float(total) >= 90
    assert "sales.monthly_revenue" in breakdown
