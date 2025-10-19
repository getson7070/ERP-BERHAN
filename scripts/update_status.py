#!/usr/bin/env python3
"""Write current operational metrics to docs/status.md."""
from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path
from typing import Any, Dict

import requests  # type: ignore[import-untyped]

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

REPO = os.environ.get("GITHUB_REPOSITORY", "getson7070/ERP-BERHAN")
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"token {TOKEN}"} if TOKEN else {}),
}


def _latest_run_id(workflow: str) -> int | None:
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow}/runs?per_page=1"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        return runs[0]["id"] if runs else None
    except Exception:
        return None


def _artifact_json(run_id: int, name: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/artifacts"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        for art in resp.json().get("artifacts", []):
            if art["name"] == name:
                dl = requests.get(
                    art["archive_download_url"], headers=HEADERS, timeout=10
                )
                with zipfile.ZipFile(io.BytesIO(dl.content)) as zf:
                    with zf.open("metrics.json") as fh:
                        return json.load(fh)
    except Exception:
        pass
    return {}


def fetch_metrics() -> Dict[str, int]:
    run_id = _latest_run_id("perf.yml")
    data = _artifact_json(run_id, "perf-metrics") if run_id else {}
    return {
        "p95_latency_ms": int(data.get("p95_latency_ms", 0)),
        "queue_lag": int(data.get("queue_lag", 0)),
        "mv_age_s": int(data.get("mv_age_s", 0)),
        "rate_limit_429s": int(data.get("rate_limit_429s", 0)),
    }


def fetch_audit_run_id() -> str:
    run_id = _latest_run_id("audit-chain.yml")
    return str(run_id) if run_id else "unknown"


def load_metrics() -> Dict[str, int]:
    artifact = os.environ.get("STATUS_ARTIFACT")
    if not artifact:
        return {
            "p95_latency_ms": 0,
            "queue_lag": 0,
            "mv_age_s": 0,
            "rl_429s": 0,
            "audit_chain_run_id": 0,
        }
    with open(artifact, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {
        "p95_latency_ms": int(data.get("p95_latency_ms", 0)),
        "queue_lag": int(data.get("queue_lag", 0)),
        "mv_age_s": int(data.get("mv_age_s", 0)),
        "rl_429s": int(data.get("rl_429s", data.get("rate_limit_429s", 0))),
        "audit_chain_run_id": int(data.get("audit_chain_run_id", 0)),
    }


def write_status(path: Path, metrics: Dict[str, int] | None = None) -> None:
    if metrics is None:
        metrics = fetch_metrics()
        metrics["audit_chain_run_id"] = int(fetch_audit_run_id())
        metrics["rl_429s"] = metrics.pop("rate_limit_429s", 0)
    content = (
        "# Status\n\n"
        "This page is updated by a scheduled GitHub Action and exposes recent operational metrics.\n\n"
        f"- **p95 API latency**: {metrics['p95_latency_ms']}ms\n"
        f"- **Queue lag**: {metrics['queue_lag']}\n"
        f"- **Materialized view freshness**: {metrics['mv_age_s']}s\n"
        f"- **Rate-limit 429s**: {metrics['rl_429s']}\n\n"
        "## How the audit chain is verified\n"
        "Nightly `audit-chain` runs compute and verify a checksum over the audit log. "
        f"See [run {metrics['audit_chain_run_id']}](https://github.com/{REPO}/actions/runs/{metrics['audit_chain_run_id']}) for details.\n\n"
        "The action also publishes a JSON artifact alongside this file for external dashboards.\n"
    )
    path.write_text(content)


def main() -> None:
    target = ROOT / "docs" / "status.md"
    write_status(target)


if __name__ == "__main__":
    main()


