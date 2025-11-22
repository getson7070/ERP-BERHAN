"""Health check package providing a shared registry and default checks."""
from __future__ import annotations

from .registry import HealthCheck, HealthRegistry, health_registry  # noqa: F401
from . import checks_core  # noqa: F401  # Registers baseline checks on import
