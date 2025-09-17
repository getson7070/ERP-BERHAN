#!/usr/bin/env python3
"""Validate OWASP ASVS traceability coverage."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

DOC_PATH = Path("docs/security/asvs_traceability.md")
DATA_PATH = Path("scripts/data/asvs_requirements.json")
ALLOWED_TYPES = {"code", "test", "runbook", "doc"}


def _load_json_block() -> list[dict]:
    text = DOC_PATH.read_text(encoding="utf-8")
    match = re.search(r"```json\s*(\[.*?\])\s*```", text, re.DOTALL)
    if not match:
        raise SystemExit("ASVS traceability document is missing the machine-readable JSON block")
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise SystemExit(f"Invalid JSON in {DOC_PATH}: {exc}") from exc


def _reference_path(ref: str) -> Path:
    base = ref.split("#", 1)[0]
    base = base.split("::", 1)[0]
    return Path(base)


def _validate_coverage(entries: Iterable[dict]) -> list[str]:
    errors: list[str] = []
    for entry in entries:
        req_id = entry.get("id")
        status = entry.get("status")
        coverage = entry.get("coverage", [])
        if status == "deleted":
            continue
        if not coverage:
            errors.append(f"{req_id}: missing coverage references")
            continue
        for item in coverage:
            ctype = item.get("type")
            reference = item.get("reference")
            if ctype not in ALLOWED_TYPES:
                errors.append(f"{req_id}: unsupported coverage type '{ctype}'")
                continue
            if not reference:
                errors.append(f"{req_id}: coverage entry missing reference")
                continue
            path = _reference_path(reference)
            if path.suffix:
                candidate = path
            else:
                candidate = path
            if not candidate.exists():
                errors.append(f"{req_id}: referenced artifact '{path}' does not exist")
    return errors


def main() -> int:
    if not DOC_PATH.exists():
        raise SystemExit(f"Missing {DOC_PATH}")
    if not DATA_PATH.exists():
        raise SystemExit(f"Missing {DATA_PATH}")

    doc_entries = _load_json_block()
    doc_index = {entry["id"]: entry for entry in doc_entries}
    if len(doc_entries) != len(doc_index):
        raise SystemExit("Duplicate requirement IDs detected in traceability document")

    expected_entries = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    expected_ids = {item["id"] for item in expected_entries if item.get("status") != "deleted"}

    missing = expected_ids - doc_index.keys()
    if missing:
        raise SystemExit(f"Traceability matrix missing coverage for: {', '.join(sorted(missing))}")

    errors = _validate_coverage(doc_entries)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(f"Validated {len(expected_ids)} ASVS requirements with coverage entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
