import os

import pytest
from sqlalchemy import text

from erp.extensions import db
from erp.health import checks_core


@pytest.fixture(autouse=True)
def _cleanup_env(monkeypatch):
    monkeypatch.delenv("ALLOW_INSECURE_DEFAULTS", raising=False)
    monkeypatch.delenv("MIGRATION_CHECK_STRICT", raising=False)
    yield
    monkeypatch.delenv("ALLOW_INSECURE_DEFAULTS", raising=False)
    monkeypatch.delenv("MIGRATION_CHECK_STRICT", raising=False)


def test_migration_check_skips_in_testing(app, monkeypatch):
    with app.app_context():
        monkeypatch.delenv("MIGRATION_CHECK_STRICT", raising=False)
        result = checks_core.db_migrations()
        assert result["ok"] is True
        assert result.get("skipped") is True


def test_migration_check_flags_unknown_revision(app, monkeypatch):
    monkeypatch.setenv("MIGRATION_CHECK_STRICT", "1")
    with app.app_context():
        connection = db.engine.connect()
        try:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
            connection.execute(
                text(
                    "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"
                )
            )
            connection.execute(text("DELETE FROM alembic_version"))
            connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES ('bogus')")
            )
            connection.commit()

            result = checks_core.db_migrations()
        finally:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
            connection.commit()
            connection.close()

        assert result["ok"] is False
        assert result["current"] == "bogus"
        assert result.get("heads")


def test_migration_check_flags_multiple_heads(app, monkeypatch):
    monkeypatch.setenv("MIGRATION_CHECK_STRICT", "1")

    class DummyScript:
        def __init__(self, heads):
            self._heads = heads

        def get_heads(self):
            return self._heads

    dummy_script = DummyScript(["h1", "h2"])

    class DummyDirectory:
        @staticmethod
        def from_config(_cfg):
            return dummy_script

    monkeypatch.setattr(checks_core, "ScriptDirectory", DummyDirectory)

    with app.app_context():
        connection = db.engine.connect()
        try:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
            connection.execute(
                text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
            )
            connection.execute(text("DELETE FROM alembic_version"))
            connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('h1')"))
            connection.commit()

            result = checks_core.db_migrations()
        finally:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
            connection.commit()
            connection.close()

        assert result["ok"] is False
        assert result["error"] == "multiple_heads_detected"
        assert result["heads"] == ["h1", "h2"]
        assert "20251212100000" in result.get("resolution", "")
