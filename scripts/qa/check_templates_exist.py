#!/usr/bin/env python3
from pathlib import Path

REQUIRED = [
    "templates/index.html",
    "templates/layout.html",
    "templates/login.html",
]

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing = [rel for rel in REQUIRED if not (root / rel).exists()]
    if missing:
        print("Missing templates:", ", ".join(missing))
        return 1
    print("All templates present.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
