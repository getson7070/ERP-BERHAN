# erp/utils/circuit.py
from __future__ import annotations
import pybreaker  # pip install pybreaker

# Basic breaker: 5 consecutive failures → open for 30s
breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="external_api_breaker",
)
