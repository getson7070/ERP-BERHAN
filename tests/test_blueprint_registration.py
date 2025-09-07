import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from erp import create_app  # noqa: E402


def test_blueprints_autoregister(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "bp.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    app.config["TESTING"] = True

    # avoid database work in analytics dashboard
    monkeypatch.setattr(
        "erp.routes.analytics.fetch_kpis",
        lambda: {
            "pending_orders": 0,
            "pending_maintenance": 0,
            "expired_tenders": 0,
            "monthly_sales": [],
        },
    )

    routes = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/dashboard" in routes
    assert "/dashboard/customize" in routes
    assert "/analytics/dashboard" in routes
    assert "/reports/builder" in routes
    assert "/plugins/sample/" in routes
    assert "/feedback/" in routes
