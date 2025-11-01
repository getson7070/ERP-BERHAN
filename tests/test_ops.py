from erp.security_hardening import safe_run, safe_call, safe_popen
import json
import subprocess
import sys
from pathlib import Path

import scripts.rotate_secrets as rotate_secrets


def test_rotate_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PASSWORD", "old")
    monkeypatch.setenv("API_KEY", "old")
    monkeypatch.setattr(rotate_secrets, "SECRETS_FILE", tmp_path / "secrets.json")
    monkeypatch.setattr(rotate_secrets, "LOG_FILE", tmp_path / "rotation.log")
    result = rotate_secrets.main()
    data = json.loads((tmp_path / "secrets.json").read_text())
    assert data == result
    assert len(data["DB_PASSWORD"]) == 32
    assert len(data["API_KEY"]) == 32
    assert (tmp_path / "rotation.log").read_text().strip() != ""


def test_dr_drill(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    safe_run(
        [sys.executable, str(repo_root / "scripts/dr_drill.py")],
        cwd=tmp_path,
        check=True,
    )
    assert (tmp_path / "dr-drill.csv").exists()



