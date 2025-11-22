"""Predictive analytics placeholders for demand and churn."""
from __future__ import annotations

from datetime import date, timedelta

from celery import shared_task

from erp.extensions import db
from erp.models import AnalyticsFact


@shared_task(name="erp.tasks.predictive.demand_forecast")
def demand_forecast(metric_key: str = "sales.monthly_revenue", horizon_days: int = 90) -> None:
    """Naive forecast that projects the last 30-day average into the future.

    Replace this with a real forecasting model (Prophet/ARIMA) once available.
    """

    org_ids = [row[0] for row in db.session.query(AnalyticsFact.org_id).filter_by(metric_key=metric_key).distinct().all()]

    for org_id in org_ids:
        series = (
            AnalyticsFact.query.filter(
                AnalyticsFact.org_id == org_id,
                AnalyticsFact.metric_key == metric_key,
            )
            .order_by(AnalyticsFact.ts_date.desc())
            .limit(30)
            .all()
        )

        if not series:
            continue

        avg_value = sum(float(row.value) for row in series) / len(series)
        start = date.today()

        for offset in range(horizon_days):
            ts_date = start + timedelta(days=offset)
            AnalyticsFact.query.filter_by(
                org_id=org_id, metric_key=f"{metric_key}.forecast", ts_date=ts_date
            ).delete()

            db.session.add(
                AnalyticsFact(
                    org_id=org_id,
                    metric_key=f"{metric_key}.forecast",
                    ts_date=ts_date,
                    value=avg_value,
                )
            )

    db.session.commit()
