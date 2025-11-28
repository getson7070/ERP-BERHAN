from http import HTTPStatus


def test_login_rate_limit_per_ip_and_email(client):
    payload = {"email": "locked@example.com", "password": "bad"}
    for _ in range(5):
        resp = client.post("/auth/login", json=payload)
        assert resp.status_code == HTTPStatus.UNAUTHORIZED

    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == HTTPStatus.TOO_MANY_REQUESTS
