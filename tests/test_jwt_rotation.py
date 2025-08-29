import json
import os
import subprocess
import sys
from pathlib import Path


def test_rotate_jwt_secret(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "rotate_jwt_secret.py"
    env = os.environ.copy()
    env.pop("JWT_SECRETS", None)
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads((tmp_path / "jwt_secrets.json").read_text())
    assert "v1" in data
    log_file = tmp_path / "logs" / "jwt_rotation.log"
    assert log_file.exists()
    assert "Rotated to v1" in result.stdout
