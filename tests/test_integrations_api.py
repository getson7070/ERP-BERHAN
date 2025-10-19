import os

os.environ["USE_FAKE_REDIS"] = "1"

from erp import create_app


def test_event_endpoint_schema_and_role(tmp_path):
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/int.db"
    app.config["API_TOKEN"] = "secret"
    app.config["SECURITY_PASSWORD_SALT"] = "salty"
    app.config["JWT_SECRET"] = "jwt-secret"
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["role"] = "Admin"
        resp = client.post(
            "/api/integrations/events",
            json={"event": "order_created", "payload": {}},
            headers={"Authorization": "Bearer secret"},
        )
        assert resp.status_code == 200
        resp_bad = client.post(
            "/api/integrations/events",
            json={"event": 123},
            headers={"Authorization": "Bearer secret"},
        )
        assert resp_bad.status_code == 400


def test_graphql_endpoint(tmp_path):
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/gql.db"
    app.config["API_TOKEN"] = "secret"
    app.config["SECURITY_PASSWORD_SALT"] = "salty"
    app.config["JWT_SECRET"] = "jwt-secret"
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["role"] = "Admin"
        resp = client.post(
            "/api/integrations/graphql",
            json={"query": "{ events { name } }"},
            headers={"Authorization": "Bearer secret"},
        )
        assert resp.status_code == 200
        assert resp.get_json() == {"events": []}


