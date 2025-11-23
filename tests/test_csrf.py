import contextlib


@contextlib.contextmanager
def _csrf_enabled(app):
    original_csrf = app.config.get("WTF_CSRF_ENABLED", False)
    original_login_disabled = app.config.get("LOGIN_DISABLED", False)
    app.config.update(WTF_CSRF_ENABLED=True, LOGIN_DISABLED=True)
    try:
        yield
    finally:
        app.config.update(
            WTF_CSRF_ENABLED=original_csrf,
            LOGIN_DISABLED=original_login_disabled,
        )


def test_csrf_blocks_post_without_token(app):
    with _csrf_enabled(app):
        with app.test_client(use_cookies=True) as client:
            # establish a session
            client.get("/api/auth/csrf")
            resp = client.post("/api/auth/csrf-check", json={})
            assert resp.status_code in (400, 403)


def test_csrf_allows_post_with_token(app):
    with _csrf_enabled(app):
        with app.test_client(use_cookies=True) as client:
            token = client.get("/api/auth/csrf").get_json()["csrf_token"]
            resp = client.post(
                "/api/auth/csrf-check",
                json={},
                headers={"X-CSRF-Token": token},
            )
            assert resp.status_code == 200
