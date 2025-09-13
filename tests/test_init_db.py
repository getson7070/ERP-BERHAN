import types
from sqlalchemy import select

import init_db
from db import get_engine


def test_init_db_seeds_core_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SEED_DEMO_DATA", "0")

    def fake_run(cmd, check):
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(init_db.subprocess, "run", fake_run)
    init_db.init_db()

    engine = get_engine()
    with engine.connect() as conn:
        regions_rows = conn.execute(select(init_db.regions)).fetchall()
        cities_rows = conn.execute(select(init_db.cities)).fetchall()
        assert regions_rows and cities_rows, "seed data missing"
