import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))  # noqa: E402

from erp import create_app  # noqa: E402


def test_mfa_protected_route(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "mfa.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["logged_in"] = True
    assert client.get("/admin/panel").status_code == 403

    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["mfa_verified"] = True
    assert client.get("/admin/panel").status_code == 200


