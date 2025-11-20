import datetime as dt


def test_sensitive_metric_requires_admin(client, db_session, resolve_org_id):
    from erp.models import AnalyticsFact, AnalyticsMetric

    org_id = resolve_org_id()
    metric = AnalyticsMetric(
        org_id=org_id,
        key="finance.cash_balance",
        name="Cash Balance",
        privacy_class="sensitive",
        source_module="finance",
    )
    db_session.add(metric)
    db_session.add(
        AnalyticsFact(
            org_id=org_id,
            metric_key=metric.key,
            ts_date=dt.date.today(),
            value=1000,
        )
    )
    db_session.commit()

    resp = client.get("/api/analytics/fact", query_string={"metric_key": metric.key})
    assert resp.status_code in (401, 403)
