import os
import subprocess
from pathlib import Path

from sqlalchemy import text

import init_db
from db import get_engine


def _run_init(tmp_path: Path, **env):
    db_path = tmp_path / "init.db"
    original_env = {k: os.environ.get(k) for k in ["DATABASE_PATH", *env.keys()]}
    os.environ["DATABASE_PATH"] = str(db_path)
    for k, v in env.items():
        os.environ[k] = v
    subprocess_run = subprocess.run
    def fake_run(*args, **kwargs):
        return subprocess_run(["true"], check=True)
    subprocess.run = fake_run  # type: ignore
    try:
        init_db.init_db()
        engine = get_engine()
    finally:
        subprocess.run = subprocess_run  # type: ignore
        for k, v in original_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return engine


def test_regions_seeded(tmp_path):
    engine = _run_init(tmp_path)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM regions")).scalar()
    assert count and count > 0


def test_demo_admin_seeded(tmp_path):
    engine = _run_init(
        tmp_path,
        SEED_DEMO_DATA="1",
        ADMIN_USERNAME="admin",
        ADMIN_PASSWORD="secret",
    )
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT username FROM users WHERE username='admin'")
        ).first()
    assert row is not None
