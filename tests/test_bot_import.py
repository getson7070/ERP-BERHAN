import importlib


def test_import_without_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    module = importlib.import_module("bot")
    assert hasattr(module, "main")


