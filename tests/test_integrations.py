import pytest

from erp.integrations import powerbi


def test_powerbi_token_roundtrip(monkeypatch):
    monkeypatch.setenv("POWERBI_TOKEN", "abc123")
    assert powerbi.get_embed_token() == "abc123"


def test_powerbi_token_missing(monkeypatch):
    monkeypatch.delenv("POWERBI_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        powerbi.get_embed_token()


