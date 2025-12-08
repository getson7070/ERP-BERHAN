"""Lightweight geospatial helpers used for distance and ETA calculations."""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt


class InvalidCoordinate(ValueError):
    """Raised when a latitude/longitude pair is invalid."""


def validate_lat_lng(lat: float | int | str, lng: float | int | str) -> tuple[float, float]:
    """Coerce and validate a latitude/longitude pair.

    Returns a tuple of floats when valid or raises :class:`InvalidCoordinate` with a
    human‑readable message when the input is out of range.
    """

    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        raise InvalidCoordinate("latitude and longitude must be numeric")

    if not (-90.0 <= lat_f <= 90.0):
        raise InvalidCoordinate("latitude must be between -90 and 90 degrees")
    if not (-180.0 <= lng_f <= 180.0):
        raise InvalidCoordinate("longitude must be between -180 and 180 degrees")

    return lat_f, lng_f


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
