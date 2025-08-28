import pathlib
import sys
import time
from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token, decode_token


def test_old_kid_valid_until_expiry(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "rot.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    monkeypatch.setenv("JWT_SECRETS", '{"v1":"old"}')
    monkeypatch.setenv("JWT_SECRET_ID", "v1")
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
    from erp import create_app

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        token = create_access_token(
            "u", expires_delta=timedelta(seconds=1), additional_headers={"kid": "v1"}
        )

    # rotate secret
    app.config["JWT_SECRETS"]["v2"] = "new"
    app.config["JWT_SECRET_ID"] = "v2"
    app.config["JWT_SECRET_KEY"] = "new"

    with app.app_context():
        assert decode_token(token)["sub"] == "u"
        time.sleep(1.1)
        with pytest.raises(Exception):
            decode_token(token)
