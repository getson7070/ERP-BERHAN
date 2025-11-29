import importlib

import pytest

import db


def test_engine_guard_enforces_database_url_in_production(monkeypatch):
    monkeypatch.setattr(db, "_engine", None)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")

    with pytest.raises(RuntimeError, match="DATABASE_URL must be set in production environments"):
        importlib.reload(db).get_engine()

