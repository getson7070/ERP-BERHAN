import pytest

from erp.health import checks_core


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    for key in (
        "ALLOW_INSECURE_DEFAULTS",
        "CONFIG_CHECK_STRICT",
        "SECRET_KEY",
        "DATABASE_URL",
        "SQLALCHEMY_DATABASE_URI",
        "JWT_SECRET_KEY",
        "FLASK_ENV",
        "ENV",
    ):
        monkeypatch.delenv(key, raising=False)
    yield
    for key in (
        "ALLOW_INSECURE_DEFAULTS",
        "CONFIG_CHECK_STRICT",
        "SECRET_KEY",
        "DATABASE_URL",
        "SQLALCHEMY_DATABASE_URI",
        "JWT_SECRET_KEY",
        "FLASK_ENV",
        "ENV",
    ):
        monkeypatch.delenv(key, raising=False)


def test_config_check_skips_in_testing(app):
    with app.app_context():
        result = checks_core.config_sanity()

    assert result["ok"] is True
    assert result.get("skipped") is True
    assert result.get("reason") == "testing_or_insecure_mode"


def test_config_check_flags_missing_and_insecure(monkeypatch, app):
    monkeypatch.setenv("CONFIG_CHECK_STRICT", "1")
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///local.db")

    with app.app_context():
        result = checks_core.config_sanity()

    assert result["ok"] is False
    assert "SECRET_KEY" in result["missing"]
    assert "JWT_SECRET_KEY" in result["missing"]
    assert result["insecure_sqlite"] is True
    assert result["production"] is True


def test_config_check_passes_with_secure_env(monkeypatch, app):
    monkeypatch.setenv("CONFIG_CHECK_STRICT", "1")
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "super-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret")

    with app.app_context():
        result = checks_core.config_sanity()

    assert result["ok"] is True
    assert result["missing"] == []
    assert result["weak_defaults"] == []
    assert result["insecure_sqlite"] is False
