from erp import create_app


def _build_app(monkeypatch):
    monkeypatch.setenv("ALLOW_INSECURE_DEFAULTS", "1")
    monkeypatch.setenv("SECRET_KEY", "dev-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    app = create_app()
    # Explicitly exercise the gate by disabling the test shortcut.
    app.config.update(TESTING=False, STRICT_ORG_BOUNDARIES=False, ALLOW_INSECURE_DEFAULTS="1")
    return app


def test_login_page_is_public(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()

    resp = client.get("/auth/login")
    assert resp.status_code == 200

    resp_alias = client.get("/login")
    assert resp_alias.status_code != 401


def test_static_assets_are_public(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()

    resp = client.get("/static/favicon.ico")
    assert resp.status_code != 401
