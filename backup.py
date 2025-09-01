import csv
import os
import shutil
import subprocess
import time
from datetime import datetime, UTC
from pathlib import Path

import boto3
from cryptography.fernet import Fernet
from celery import shared_task
from prometheus_client import Gauge


BACKUP_LAST_SUCCESS = Gauge(
    "backup_last_success_timestamp",
    "Unix timestamp of the last successful backup",
)


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
        subprocess.run(
            ["mysqldump", db_url, "--result-file", str(dump_file)], check=True
        )
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


def _latest_backup(backup_dir: Path) -> Path:
    backups = sorted(backup_dir.glob("*.sqlite")) + sorted(
        backup_dir.glob("*.sql*"), reverse=True
    )
    if not backups:
        raise FileNotFoundError("No backups found")
    return backups[-1]


def _log_drill(start: float, backup_file: Path, log_dir: Path = Path("logs")):
    end = time.time()
    rpo = int(start - backup_file.stat().st_mtime)
    rto = int(end - start)
    log_dir.mkdir(exist_ok=True)
    with open(log_dir / "restore_drill.log", "a", newline="") as fh:
        writer = csv.writer(fh)
        if fh.tell() == 0:
            writer.writerow(
                ["start_iso", "end_iso", "rpo_seconds", "rto_seconds", "backup_file"]
            )
        writer.writerow(
            [
                datetime.utcfromtimestamp(start).isoformat(),
                datetime.utcfromtimestamp(end).isoformat(),
                rpo,
                rto,
                backup_file.name,
            ]
        )


@shared_task(name="backup.run_backup")
def run_backup():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is required for backups")
    create_backup(db_url)
    BACKUP_LAST_SUCCESS.set(time.time())


def perform_restore_drill():
    """Restore the most recent backup and log RPO/RTO metrics."""
    db_url = os.environ.get("DR_RESTORE_DATABASE_URL") or os.environ.get(
        "DATABASE_URL"
    )
    if not db_url:
        raise RuntimeError("DATABASE_URL is required for restore drill")
    backup_dir = Path(os.environ.get("BACKUP_DIR", "backups"))
    backup_file = _latest_backup(backup_dir)
    start = time.time()
    restore_backup(db_url, backup_file)
    _log_drill(start, backup_file)


@shared_task(name="backup.run_restore_drill")
def run_restore_drill():
    perform_restore_drill()
