import json
import os
import runpy
from pathlib import Path


def test_rotate_jwt_secret(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JWT_SECRETS", "{}")
    script = Path(__file__).resolve().parents[1] / "scripts" / "rotate_jwt_secret.py"
    runpy.run_path(str(script))
    secrets = json.loads((tmp_path / "jwt_secrets.json").read_text())
    assert "v1" in secrets
    assert os.environ["JWT_SECRET_ID"] == "v1"
    log = (tmp_path / "logs" / "jwt_rotation.log").read_text()
    assert "v1" in log
