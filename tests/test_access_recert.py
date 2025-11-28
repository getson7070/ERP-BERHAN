import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import erp.data_retention as data_retention  # noqa: E402
from erp.data_retention import run_access_recert_export  # noqa: E402


def test_access_recert_export_creates_readonly_file(tmp_path, monkeypatch):
    def _write_export():
        path = Path("access_recert.csv")
        path.write_text("dummy export")
        path.chmod(0o444)
        return path

    monkeypatch.setattr(data_retention, "export_recert", _write_export)
    monkeypatch.chdir(tmp_path)
    result = run_access_recert_export()
    p = Path(result)
    assert p.exists()
    assert oct(p.stat().st_mode & 0o777) == "0o444"


def test_run_access_recert_export_handles_missing_helper(monkeypatch):
    monkeypatch.setattr(data_retention, "export_recert", None)
    result = run_access_recert_export()
    assert "unavailable" in result


