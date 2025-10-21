"""
Very small stub for analytics.retrain_and_predict used in tests.
"""
from __future__ import annotations
from statistics import mean

_MODEL_VERSION = 0

def retrain_and_predict(series: list[float]) -> dict:
    global _MODEL_VERSION
    _MODEL_VERSION += 1
    avg = float(mean(series)) if series else 0.0
    # pretend to forecast next 3 points
    return {"model_version": _MODEL_VERSION, "forecast": [avg, avg, avg]}