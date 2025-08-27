import os
import shutil
import subprocess
from datetime import datetime, UTC
from pathlib import Path

import boto3
from cryptography.fernet import Fernet


def create_backup(db_url, backup_dir="backups"):
    """Create an encrypted backup and optionally upload to S3.

    For SQLite URLs, the database file is copied. For PostgreSQL and MySQL
    URLs, ``pg_dump`` or ``mysqldump`` are executed to generate SQL dumps.
    If ``BACKUP_ENCRYPTION_KEY`` is set, the dump is encrypted with Fernet and
    an ``.enc`` file is produced. When ``S3_BUCKET`` is configured, the backup
    is uploaded using ``boto3`` to the provided bucket.
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

    key = os.environ.get("BACKUP_ENCRYPTION_KEY")
    if key:
        with open(dump_file, "rb") as fh:
            token = Fernet(key.encode()).encrypt(fh.read())
        enc_file = dump_file.with_suffix(dump_file.suffix + ".enc")
        with open(enc_file, "wb") as fh:
            fh.write(token)
        dump_file = enc_file

    bucket = os.environ.get("S3_BUCKET")
    if bucket:
        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ.get("S3_ENDPOINT"),
            region_name=os.environ.get("AWS_REGION"),
        )
        s3.upload_file(str(dump_file), bucket, dump_file.name)

    return dump_file


def restore_backup(db_url, backup_file):
    """Restore a database from a backup file."""
    if db_url.startswith("sqlite:///"):
        dest = db_url.replace("sqlite:///", "")
        shutil.copy(backup_file, dest)
        return dest
    raise ValueError("Restore supported only for sqlite databases")
