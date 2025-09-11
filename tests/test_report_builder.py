from erp import create_app
from erp.extensions import db


def _setup_app(tmp_path, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "test")
    monkeypatch.setenv("JWT_SECRET", "test")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'reports.db'}")
    monkeypatch.setenv("REPORTS_ENABLED", "1")
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.app_context():
        db.create_all()
    return app


def test_builder_get(tmp_path, monkeypatch):
    app = _setup_app(tmp_path, monkeypatch)
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["org_id"] = 1
        sess["logged_in"] = True
    rv = client.get("/reports/builder")
    assert rv.status_code == 200


def test_run_report_post(tmp_path, monkeypatch):
    app = _setup_app(tmp_path, monkeypatch)
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["org_id"] = 1
        sess["logged_in"] = True
    rv = client.post("/reports/run", json={"config": {}})
    assert rv.status_code == 200
    assert rv.get_json()["data"] == []
