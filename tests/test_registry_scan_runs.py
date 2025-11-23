import os
import subprocess
import sys


def test_registry_scan_script_executes(monkeypatch):
    env = os.environ.copy()
    env["REGISTRY_SCAN_SKIP_APP"] = "1"
    result = subprocess.run([sys.executable, "tools/scan_registry.py"], env=env)
    assert result.returncode == 0


def test_migration_docs_checker_executes():
    env = os.environ.copy()
    env["ALLOW_MISSING_MIGRATION_DOCS"] = "1"
    result = subprocess.run([sys.executable, "tools/check_migration_docs.py"], env=env)
    assert result.returncode == 0
