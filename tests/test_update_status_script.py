import runpy
from pathlib import Path


def load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "update_status.py"
    return runpy.run_path(str(path), run_name="mod")


def test_write_status(tmp_path):
    mod = load_module()
    mod["write_status"].__globals__["fetch_metrics"] = lambda: {
        "p95_latency_ms": 10,
        "queue_lag": 1,
        "mv_age_s": 2,
        "rate_limit_429s": 3,
    }
    mod["write_status"].__globals__["fetch_audit_run_id"] = lambda: "42"
    target = tmp_path / "status.md"
    mod["write_status"](target)
    text = target.read_text()
    assert "10ms" in text
    assert "1" in text
    assert "2s" in text
    assert "3" in text
    assert "run 42" in text


