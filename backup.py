import os
import shutil
import subprocess
from datetime import datetime, UTC
from pathlib import Path

def create_backup(db_url, backup_dir="backups"):
    """Create a timestamped backup for the given database URL.

    For SQLite URLs, the database file is copied. For PostgreSQL and MySQL
    URLs, ``pg_dump`` or ``mysqldump`` are executed to generate SQL dumps.
    Returns the path to the created backup file.
    """
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    if db_url.startswith("sqlite:///"):
        src = db_url.replace("sqlite:///", "")
        dest = backup_path / f"{timestamp}.sqlite"
        shutil.copy(src, dest)
        return dest

    dump_file = backup_path / f"{timestamp}.sql"
    if db_url.startswith("postgresql"):
        subprocess.run(["pg_dump", db_url, "-f", str(dump_file)], check=True)
    elif db_url.startswith("mysql"):
        subprocess.run(["mysqldump", db_url, "--result-file", str(dump_file)], check=True)
    else:
        raise ValueError("Unsupported database URL")
    return dump_file


def restore_backup(db_url, backup_file):
    """Restore a database from a backup file."""
    if db_url.startswith("sqlite:///"):
        dest = db_url.replace("sqlite:///", "")
        shutil.copy(backup_file, dest)
        return dest
    raise ValueError("Restore supported only for sqlite databases")
