import shutil
import subprocess
import sys
from pathlib import Path


def test_rotate_jwt_secret(tmp_path):
    script = (
        Path(__file__).resolve().parents[1]
        / 'scripts'
        / 'rotate_jwt_secret.py'
    )
    dst = tmp_path / 'rotate_jwt_secret.py'
    shutil.copy(script, dst)
    subprocess.check_call([sys.executable, str(dst)], cwd=tmp_path)
    assert (tmp_path / 'jwt_secrets.json').exists()
    assert (tmp_path / 'logs' / 'jwt_rotation.log').exists()
