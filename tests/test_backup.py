from pathlib import Path
from unittest.mock import patch
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backup import create_backup


def test_pg_dump_invoked(tmp_path):
    db_url = 'postgresql://user:pass@localhost/db'

    def fake_run(cmd, check):
        Path(cmd[cmd.index('-f') + 1]).write_text('-- pg dump --')

    with patch('subprocess.run', side_effect=fake_run) as run:
        backup_file = create_backup(db_url, backup_dir=tmp_path)
        assert run.called
        assert backup_file.exists()


def test_mysql_dump_invoked(tmp_path):
    db_url = 'mysql://user:pass@localhost/db'

    def fake_run(cmd, check):
        Path(cmd[-1]).write_text('-- mysql dump --')

    with patch('subprocess.run', side_effect=fake_run) as run:
        backup_file = create_backup(db_url, backup_dir=tmp_path)
        assert run.called
        assert backup_file.exists()
