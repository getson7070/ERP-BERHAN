from erp import create_app

def test_security_cookies():
    app = create_app()
    assert app.config.get("SESSION_COOKIE_HTTPONLY") is True
    assert app.config.get("SESSION_COOKIE_SECURE") is True
    assert app.config.get("SESSION_COOKIE_SAMESITE") in {"Lax","Strict","None"}
