"""Health check registry for lightweight service diagnostics."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable
import time


@dataclass
class HealthCheck:
    """Registered health check definition."""

    name: str
    fn: Callable[[], dict[str, Any]]
    timeout_s: float = 2.0
    critical: bool = True


class HealthRegistry:
    """In-memory registry that executes registered health checks."""

    def __init__(self) -> None:
        self._checks: "OrderedDict[str, HealthCheck]" = OrderedDict()

    def register(self, check: HealthCheck) -> None:
        """Register or replace a health check by name."""

        self._checks[check.name] = check

    def run_all(self) -> tuple[bool, dict[str, dict[str, Any]]]:
        """Run all checks and return the overall status and per-check details."""

        results: dict[str, dict[str, Any]] = {}
        overall_ok = True

        for name, check in self._checks.items():
            start = time.time()
            ok = True
            detail: dict[str, Any] = {}
            error: str | None = None

            try:
                detail = check.fn() or {}
                ok = bool(detail.get("ok", True))
            except Exception as exc:  # pragma: no cover - defensive guard
                ok = False
                error = str(exc)

            duration = time.time() - start
            results[name] = {
                "ok": ok,
                "critical": check.critical,
                "duration_ms": int(duration * 1000),
                "detail": detail,
                "error": error,
            }

            if check.critical and not ok:
                overall_ok = False

        return overall_ok, results


health_registry = HealthRegistry()
