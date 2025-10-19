
from db import get_dialect


def test_detect_postgres(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost/db")
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    assert get_dialect() == "postgresql"


def test_detect_sqlite(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "t.db"))
    assert get_dialect() == "sqlite"


