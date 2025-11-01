from erp.security_hardening import safe_run, safe_call, safe_popen
import json
import subprocess
import sys
from pathlib import Path


def test_rotate_jwt_secret_script(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    script = Path(__file__).resolve().parents[1] / "scripts" / "rotate_jwt_secret.py"
    result = safe_run(
        [sys.executable, str(script)], capture_output=True, text=True, check=True
    )
    assert "Rotated to v1" in result.stdout
    data = json.loads((tmp_path / "jwt_secrets.json").read_text())
    assert "v1" in data
    assert (tmp_path / "logs" / "jwt_rotation.log").exists()



