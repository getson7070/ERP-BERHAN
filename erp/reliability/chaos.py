"""Opt-in chaos injection utilities for failure drills."""
from __future__ import annotations

import os
import random


def chaos_enabled(feature: str) -> bool:
    return os.getenv(f"CHAOS_{feature.upper()}", "0") == "1"


def maybe_fail(feature: str) -> None:
    if not chaos_enabled(feature):
        return
    rate = float(os.getenv("CHAOS_RATE", "0.3"))
    if random.random() < rate:
        raise RuntimeError(f"CHAOS injected failure for {feature}")


def apply_chaos_to_external_calls() -> None:
    for feature in ("banking", "telegram", "email"):
        maybe_fail(feature)
