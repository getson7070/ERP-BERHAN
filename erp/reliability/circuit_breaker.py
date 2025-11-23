"""Lightweight circuit breaker to protect external dependencies."""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 5
    reset_timeout_s: int = 60
    half_open_success: int = 2

    state: str = field(default="closed")
    failures: int = field(default=0)
    successes: int = field(default=0)
    opened_at: float | None = field(default=None)

    def allow(self) -> bool:
        if self.state == "closed":
            return True

        if self.state == "open":
            if self.opened_at and (time.time() - self.opened_at) > self.reset_timeout_s:
                self.state = "half_open"
                self.failures = 0
                self.successes = 0
                return True
            return False

        return True

    def record_success(self) -> None:
        if self.state == "half_open":
            self.successes += 1
            if self.successes >= self.half_open_success:
                self.state = "closed"
                self.failures = 0
        else:
            self.failures = 0

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "open"
            self.opened_at = time.time()


_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(name: str) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name=name)
    return _breakers[name]
