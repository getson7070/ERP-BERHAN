from __future__ import annotations

import json

import scripts.update_status as update_status


def test_write_status(tmp_path, monkeypatch):
    metrics = {
        "p95_latency_ms": 123,
        "queue_lag": 4,
        "mv_age_s": 7,
        "rl_429s": 2,
        "audit_chain_run_id": 999,
    }
    artifact = tmp_path / "metrics.json"
    artifact.write_text(json.dumps(metrics))
    monkeypatch.setenv("STATUS_ARTIFACT", str(artifact))

    loaded = update_status.load_metrics()
    assert loaded == metrics

    out_file = tmp_path / "status.md"
    update_status.write_status(out_file, loaded)
    content = out_file.read_text()
    assert "p95 API latency" in content
    assert "Queue lag" in content
    assert "Materialized view freshness" in content
    assert "Rate-limit 429s" in content
    assert str(metrics["audit_chain_run_id"]) in content
