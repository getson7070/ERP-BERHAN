import json
from pathlib import Path


def load_metrics() -> dict:
    """
    Minimal stub to return a fake metrics snapshot.
    Real implementation can be wired to Prometheus, DB, etc.
    """
    return {"uptime": 99.9, "healthy": True}


def write_status(metrics: dict) -> None:
    """
    Writes a JSON status file so tests / monitoring can consume it.
    """
    Path("status.json").write_text(json.dumps(metrics), encoding="utf-8")


if __name__ == "__main__":
    write_status(load_metrics())
