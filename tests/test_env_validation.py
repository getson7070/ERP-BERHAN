import os
import pytest
from erp.config_ext.validate_env import validate_required_env

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
