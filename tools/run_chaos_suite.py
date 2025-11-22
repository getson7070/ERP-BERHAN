#!/usr/bin/env python
"""Run a minimal chaos suite with opt-in env toggles."""
from __future__ import annotations

import os
import subprocess
import sys


def main() -> None:
    env = os.environ.copy()
    env.setdefault("CHAOS_BANKING", "1")
    env.setdefault("CHAOS_TELEGRAM", "1")
    env.setdefault("CHAOS_RATE", "0.4")

    print("Chaos toggles enabled; executing smoke suite...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/smoke"], env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
