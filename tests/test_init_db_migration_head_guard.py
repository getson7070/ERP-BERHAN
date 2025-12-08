import pytest

import init_db


def test_assert_single_migration_head_allows_single(monkeypatch):
    monkeypatch.setattr(init_db, "_get_migration_heads", lambda: ["abc123"])

    heads = init_db._assert_single_migration_head()

    assert heads == ["abc123"]


def test_assert_single_migration_head_raises_on_multiple(monkeypatch):
    monkeypatch.setattr(init_db, "_get_migration_heads", lambda: ["h1", "h2", "h1"])

    with pytest.raises(RuntimeError) as excinfo:
        init_db._assert_single_migration_head()

    message = str(excinfo.value)
    assert "Multiple Alembic heads" in message
    assert "h1, h2" in message
    assert "20251212100000" in message
