from erp import create_app
from erp.extensions import db
from erp.models import Recruitment, PerformanceReview


def _setup_app(tmp_path, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "test")
    monkeypatch.setenv("JWT_SECRET", "test")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'hr.db'}")
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.app_context():
        db.create_all()
    return app


def test_recruitment_flow(tmp_path, monkeypatch):
    app = _setup_app(tmp_path, monkeypatch)
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["org_id"] = 1
        sess["logged_in"] = True
    response = client.post(
        "/hr/recruitment",
        data={"candidate_name": "Alice", "position": "Engineer"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Recruitment.query.count() == 1


def test_performance_flow(tmp_path, monkeypatch):
    app = _setup_app(tmp_path, monkeypatch)
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["org_id"] = 1
        sess["logged_in"] = True
    response = client.post(
        "/hr/performance",
        data={"employee_name": "Bob", "score": "5"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert PerformanceReview.query.count() == 1
