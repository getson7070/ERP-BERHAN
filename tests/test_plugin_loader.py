import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app


def test_plugin_loaded_and_listed():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    resp = client.get("/plugins/sample/")
    assert resp.status_code == 200
    assert b"sample plugin" in resp.data

    listing = client.get("/plugins/")
    assert listing.status_code == 200
    assert b"sample_plugin" in listing.data
    assert any(p["name"] == "sample_plugin" for p in app.config["PLUGIN_REGISTRY"])


def test_plugin_blocked_when_not_allowlisted(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "allowed.py").write_text(
        "def register(app, registry):\n    registry('allowed')\n"
    )
    (plugin_dir / "blocked.py").write_text(
        "def register(app, registry):\n    registry('blocked')\n"
    )
    app = create_app()
    app.config.update({
        "PLUGIN_PATH": str(plugin_dir),
        "PLUGIN_ALLOWLIST": ["allowed"],
    })
    from erp.plugins import load_plugins

    load_plugins(app)
    loaded = app.config["LOADED_PLUGINS"]
    assert "allowed" in loaded
    assert "blocked" not in loaded


def test_plugin_sandbox_blocks_unsafe_calls(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "danger.py").write_text(
        "def register(app, registry):\n    open('x', 'w')\n"
    )
    app = create_app()
    app.config.update({
        "PLUGIN_PATH": str(plugin_dir),
        "PLUGIN_SANDBOX_ENABLED": True,
        "PLUGIN_ALLOWLIST": ["danger"],
    })
    from erp.plugins import load_plugins

    load_plugins(app)
    loaded = app.config["LOADED_PLUGINS"]
    assert "danger" not in loaded
