from erp import create_app


def test_feedback_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'f.db'}")
    app = create_app()
    with app.test_client() as client:
        assert client.get('/feedback/').status_code == 200
        resp = client.post('/feedback/', json={'message': 'hi'})
        assert resp.status_code == 204
