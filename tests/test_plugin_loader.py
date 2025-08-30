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
