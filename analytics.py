"""
Top-level analytics compatibility shim.

Provides an ``analytics.ml`` pseudo-module so legacy imports like
``from analytics.ml import DemandForecaster`` continue to work,
while the real implementation lives in :mod:`erp.analytics`.
"""
from __future__ import annotations

import sys
import types

from erp.analytics import (
    DemandForecaster,
    InventoryAnomalyDetector,
    retrain_and_predict,
    materialized_view_state,
)

# Create a virtual "analytics.ml" module that proxies the public API
_ml = types.ModuleType("analytics.ml")
_ml.DemandForecaster = DemandForecaster
_ml.InventoryAnomalyDetector = InventoryAnomalyDetector

# Register the submodule so ``import analytics.ml`` succeeds
sys.modules[__name__ + ".ml"] = _ml

__all__ = [
    "DemandForecaster",
    "InventoryAnomalyDetector",
    "retrain_and_predict",
    "materialized_view_state",
]
