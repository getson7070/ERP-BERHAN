import json
import subprocess
from pathlib import Path


def test_rotate_jwt_secret_script(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "rotate_jwt_secret.py"
    subprocess.check_call(["python", str(script)], cwd=tmp_path)
    secrets_file = tmp_path / "jwt_secrets.json"
    log_file = tmp_path / "logs" / "jwt_rotation.log"
    data = json.loads(secrets_file.read_text())
    assert list(data.keys()) == ["v1"]
    assert log_file.exists()
    subprocess.check_call(["python", str(script)], cwd=tmp_path)
    data = json.loads(secrets_file.read_text())
    assert list(data.keys()) == ["v1", "v2"]
    assert len(log_file.read_text().strip().splitlines()) == 2


