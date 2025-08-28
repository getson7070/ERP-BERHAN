from pathlib import Path

from erp.data_retention import run_access_recert_export


def test_access_recert_export_creates_readonly_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_access_recert_export()
    p = Path(result)
    assert p.exists()
    assert oct(p.stat().st_mode & 0o777) == "0o444"
