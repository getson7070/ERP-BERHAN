"""Lightweight geospatial helpers used for distance and ETA calculations."""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt


def haversine_m(lat1, lng1, lat2, lng2) -> float:
    """Return the great-circle distance between two coordinates in meters."""

    R = 6371000.0
    lat1, lng1, lat2, lng2 = map(radians, map(float, [lat1, lng1, lat2, lng2]))
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


def eta_seconds(distance_m: float, avg_speed_mps: float | None = None) -> int:
    """Estimate ETA (in seconds) given distance and optional observed speed."""

    speed = float(avg_speed_mps or 7.0)
    if speed <= 0.5:
        speed = 7.0
    return int(distance_m / speed) if distance_m > 0 else 0
