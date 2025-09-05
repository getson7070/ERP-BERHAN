#!/usr/bin/env python3
"""Export active users and roles to an immutable CSV file."""
from __future__ import annotations

import csv
from datetime import datetime, UTC
from pathlib import Path

from erp import create_app
from erp.models import User


def export(directory: str = "exports") -> Path:
    app = create_app()
    with app.app_context():
        rows = [(u.email, ",".join(r.name for r in u.roles)) for u in User.query.all()]
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"access_recert_{datetime.now(UTC).date()}.csv"
    with output.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["email", "roles"])
        writer.writerows(rows)
    output.chmod(0o444)
    return output


if __name__ == "__main__":
    export()
