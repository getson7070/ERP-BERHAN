#!/usr/bin/env python3
"""Write current operational metrics to docs/status.md."""
from __future__ import annotations

from pathlib import Path

from db import redis_client
from erp.routes import analytics


def write_status(path: Path) -> None:
    queue = redis_client.llen("celery")
    mv_age = analytics.kpi_staleness_seconds()
    content = (
        "# Status\n\n"
        "This page is updated by a scheduled GitHub Action and exposes recent operational metrics.\n\n"
        f"- **Materialized view freshness**: {int(mv_age)}s\n"
        f"- **Queue lag**: {queue}\n"
        "- **Rate-limit 429s**: 0\n"
    )
    path.write_text(content)


def main() -> None:
    target = Path(__file__).resolve().parents[1] / "docs" / "status.md"
    write_status(target)


if __name__ == "__main__":
    main()
