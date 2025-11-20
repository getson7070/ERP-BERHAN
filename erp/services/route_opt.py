"""Route optimization with caching and provider fallbacks."""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from flask import current_app

from erp.extensions import db
from erp.models import GeoRouteCache
from erp.services.geo_utils import eta_seconds, haversine_m


def _cache_key(origin: dict[str, Any], dest: dict[str, Any], waypoints: list[dict[str, Any]] | None) -> str:
    payload = json.dumps({"o": origin, "d": dest, "w": waypoints or []}, sort_keys=True)
    return sha256(payload.encode("utf-8")).hexdigest()


def optimize_route(
    org_id: int,
    origin: dict[str, Any],
    dest: dict[str, Any],
    waypoints: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a cached or freshly computed route structure.

    Falls back to an internal haversine-based route when external providers are
    unavailable. Results are cached per (org, origin, dest, waypoints).
    """

    waypoints = waypoints or []
    key = _cache_key(origin, dest, waypoints)

    cached = GeoRouteCache.query.filter_by(org_id=org_id, cache_key=key).first()
    if cached:
        return cached.route_json

    token = current_app.config.get("MAPBOX_TOKEN")
    if token:
        # Placeholder: wire Mapbox Directions here when credentials are available.
        # This block intentionally falls through if the provider is unreachable.
        pass

    route_points = [origin] + waypoints + [dest]
    distance = 0.0
    for i in range(len(route_points) - 1):
        a = route_points[i]
        b = route_points[i + 1]
        distance += haversine_m(a["lat"], a["lng"], b["lat"], b["lng"])

    eta = eta_seconds(distance)
    route_json = {
        "provider": "internal",
        "points": route_points,
        "distance_m": distance,
        "eta_seconds": eta,
    }

    db.session.add(
        GeoRouteCache(
            org_id=org_id,
            cache_key=key,
            provider="internal",
            route_json=route_json,
            distance_meters=int(distance),
            eta_seconds=int(eta),
        )
    )
    db.session.commit()
    return route_json
