from http import HTTPStatus

from erp import create_app


def _build_app(monkeypatch, strict=True):
    monkeypatch.setenv("SECRET_KEY", "dev-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    app = create_app()
    app.config.update(
        TESTING=False,
        STRICT_ORG_BOUNDARIES=strict,
        ALLOW_INSECURE_DEFAULTS="0",
    )
    return app


def test_health_is_allowlisted_without_org(monkeypatch):
    app = _build_app(monkeypatch, strict=True)
    client = app.test_client()

    resp = client.get("/health")
    assert resp.status_code == HTTPStatus.OK

    resp_ready = client.get("/health/ready")
    assert resp_ready.status_code == HTTPStatus.OK


def test_login_allowlisted_without_org(monkeypatch):
    app = _build_app(monkeypatch, strict=True)
    client = app.test_client()

    resp = client.get("/auth/login")
    assert resp.status_code != HTTPStatus.BAD_REQUEST

    resp_alias = client.get("/login")
    assert resp_alias.status_code != HTTPStatus.BAD_REQUEST


def test_root_redirects_without_org(monkeypatch):
    app = _build_app(monkeypatch, strict=True)
    client = app.test_client()

    resp = client.get("/", headers={"Accept": "text/html"})
    assert resp.status_code in {HTTPStatus.MOVED_PERMANENTLY, HTTPStatus.FOUND, HTTPStatus.SEE_OTHER}
    assert "/auth/login" in (resp.location or "")
