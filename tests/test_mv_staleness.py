from erp import create_app
from erp.routes import analytics


def test_mv_staleness_metric(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'test.db'}")
    app = create_app()
    with app.app_context():
        monkeypatch.setattr(analytics, "kpi_staleness_seconds", lambda: 7.0)
        client = app.test_client()
        resp = client.get("/metrics")
    assert b"kpi_sales_mv_age_seconds 7.0" in resp.data
