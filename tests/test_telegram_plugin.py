import types
import pytest
from plugins import telegram_bot

telegram = pytest.importorskip("telegram")  # noqa: F401


def test_plugin_registers(monkeypatch):
    called = {}

    def fake_register(name, jobs=None):
        called["name"] = name
        called["jobs"] = jobs or []

    app = types.SimpleNamespace(config={"TELEGRAM_TOKEN": "x"})
    telegram_bot.register(app, fake_register)
    assert called["name"] == "telegram_bot"
    assert called["jobs"]


