from pathlib import Path
from unittest.mock import patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backup import create_backup, run_backup, BACKUP_LAST_SUCCESS


def test_pg_dump_invoked(tmp_path):
    db_url = os.environ.get("DATABASE_URL", os.environ.get("DATABASE_URL", os.environ.get("DATABASE_URL","postgresql+psycopg://erp:erp@db:5432/erp")))

    def fake_run(cmd, check):
        Path(cmd[cmd.index("-f") + 1]).write_text("-- pg dump --")

    with patch("subprocess.run", side_effect=fake_run) as run:
        backup_file = create_backup(db_url, backup_dir=tmp_path)
        assert run.called
        assert backup_file.exists()


def test_mysql_dump_invoked(tmp_path):
    db_url = "mysql://user:pass@localhost/db"

    def fake_run(cmd, check):
        Path(cmd[-1]).write_text("-- mysql dump --")

    with patch("subprocess.run", side_effect=fake_run) as run:
        backup_file = create_backup(db_url, backup_dir=tmp_path)
        assert run.called
        assert backup_file.exists()


def test_run_backup_sets_metric(tmp_path, monkeypatch):
    db_file = tmp_path / "db.sqlite"
    db_file.write_text("data")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    run_backup()
    assert BACKUP_LAST_SUCCESS._value.get() > 0





