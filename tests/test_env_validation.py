import importlib
import os
import sys

import pytest

from erp.config_ext.validate_env import validate_required_env


def _reload_config_module():
    sys.modules.pop("config", None)
    return importlib.import_module("config")

def test_validate_env_missing(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(SystemExit):
        validate_required_env(["SECRET_KEY"])

def test_validate_env_ok(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x")
    try:
        validate_required_env(["SECRET_KEY"])
    except SystemExit:
        pytest.fail("validate_required_env raised unexpectedly")


def test_config_rejects_default_secret_in_production(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example/db")

    with pytest.raises(RuntimeError):
        _reload_config_module()

    sys.modules.pop("config", None)


def test_config_allows_defaults_in_development(monkeypatch):
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.setenv("ENV", "development")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    cfg_module = _reload_config_module()

    assert cfg_module.Config.SECRET_KEY == "change-me-in-prod"
    assert cfg_module.Config.SQLALCHEMY_DATABASE_URI == "sqlite:///local.db"

    sys.modules.pop("config", None)


