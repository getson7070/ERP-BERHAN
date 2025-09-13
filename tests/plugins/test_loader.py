from erp import create_app
from erp.plugins import load_plugins


def test_loader_without_exec(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    plugin_file = plugins_dir / "sample.py"
    plugin_file.write_text("def register(app, registry):\n    registry('sample', {})\n")

    app = create_app()
    app.config["PLUGIN_PATH"] = str(plugins_dir)
    app.config["PLUGIN_ALLOWLIST"] = []
    app.config["PLUGIN_SANDBOX_ENABLED"] = True

    loaded = load_plugins(app)
    assert "sample" in loaded
