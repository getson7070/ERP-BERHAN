#!/usr/bin/env python3
"""Write current operational metrics to docs/status.md."""
from __future__ import annotations

import json
import os
from pathlib import Path


def load_metrics() -> dict[str, int]:
    """Load metrics from a workflow artifact.

    The GitHub Action downloads metrics into ``STATUS_ARTIFACT`` which defaults
    to ``docs/status_metrics.json``.
    """
    artifact = Path(
        os.environ.get(
            "STATUS_ARTIFACT",
            Path(__file__).resolve().parents[1] / "docs" / "status_metrics.json",
        )
    )
    if artifact.exists():
        return json.loads(artifact.read_text())
    return {}


def write_status(path: Path, metrics: dict[str, int]) -> None:
    content = (
        "# Status\n\n"
        "This page is updated by a scheduled GitHub Action and exposes recent operational metrics.\n\n"
        f"- **p95 API latency**: {metrics.get('p95_latency_ms', 'unknown')}ms\n"
        f"- **Queue lag**: {metrics.get('queue_lag', 'unknown')}\n"
        f"- **Materialized view freshness**: {metrics.get('mv_age_s', 'unknown')}s\n"
        f"- **Rate-limit 429s**: {metrics.get('rl_429s', 'unknown')}\n\n"
        "The action also publishes a JSON artifact alongside this file for external dashboards.\n\n"
        "### How the audit chain is verified\n"
        f"The [audit-chain workflow run](https://github.com/getson7070/ERP-BERHAN/actions/runs/{metrics.get('audit_chain_run_id', 'unknown')}) checks hash-chain integrity nightly.\n"
    )
    path.write_text(content)


def main() -> None:
    target = Path(__file__).resolve().parents[1] / "docs" / "status.md"
    metrics = load_metrics()
    write_status(target, metrics)


if __name__ == "__main__":
    main()
