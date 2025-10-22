# Top-level shim so tests importing `analytics` see the `erp.analytics` API.
from erp.analytics import (
    DemandForecaster,
    InventoryAnomalyDetector,
    retrain_and_predict,
    materialized_view_state,
)
__all__ = [
    "DemandForecaster",
    "InventoryAnomalyDetector",
    "retrain_and_predict",
    "materialized_view_state",
]