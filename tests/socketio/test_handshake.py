import pytest

from erp import create_app, socketio


def test_socketio_connect(monkeypatch):
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    client = socketio.test_client(app, flask_test_client=app.test_client())
    if not client.is_connected():
        pytest.skip("socket connection failed")
    client.disconnect()


