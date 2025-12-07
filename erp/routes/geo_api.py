"""Geolocation APIs for live tracking, ETA, and assignments."""
from __future__ import annotations

from http import HTTPStatus
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.audit import log_audit
from erp.extensions import db
from erp.models import GeoAssignment, GeoLastLocation, GeoPing, MarketingConsent
from erp.security import require_login, require_roles
from erp.services.geo_utils import eta_seconds, haversine_m
from erp.services.route_opt import optimize_route
from erp.utils import resolve_org_id

bp = Blueprint("geo_api", __name__, url_prefix="/api/geo")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_last_location(loc: GeoLastLocation) -> Dict[str, Any]:
    """Serialize a GeoLastLocation into a JSON-safe dict."""
    return {
        "id": getattr(loc, "id", None),
        "org_id": getattr(loc, "org_id", None),
        "subject_type": getattr(loc, "subject_type", None),
        "subject_id": getattr(loc, "subject_id", None),
        "lat": float(getattr(loc, "lat", 0.0)) if getattr(loc, "lat", None) is not None else None,
        "lng": float(getattr(loc, "lng", 0.0)) if getattr(loc, "lng", None) is not None else None,
        "accuracy_m": getattr(loc, "accuracy_m", None),
        "speed_mps": getattr(loc, "speed_mps", None),
        "heading_deg": getattr(loc, "heading_deg", None),
        "updated_at": getattr(loc, "updated_at", None).isoformat()
        if getattr(loc, "updated_at", None)
        else None,
    }


def _serialize_assignment(a: GeoAssignment) -> Dict[str, Any]:
    """Serialize a GeoAssignment into a JSON-safe dict."""
    return {
        "id": getattr(a, "id", None),
        "org_id": getattr(a, "org_id", None),
        "subject_type": getattr(a, "subject_type", None),
        "subject_id": getattr(a, "subject_id", None),
        "task_type": getattr(a, "task_type", None),
        "task_id": getattr(a, "task_id", None),
        "dest_lat": float(getattr(a, "dest_lat", 0.0)) if getattr(a, "dest_lat", None) is not None else None,
        "dest_lng": float(getattr(a, "dest_lng", 0.0)) if getattr(a, "dest_lng", None) is not None else None,
        "started_at": getattr(a, "started_at", None),
        "completed_at": getattr(a, "completed_at", None),
        "created_by_id": getattr(a, "created_by_id", None),
    }


def _has_location_consent(org_id: int, subject_type: str, subject_id: int) -> bool:
    """Return True if the subject has opted into location tracking.

    For internal field staff (sales / marketing) self-tracking, consent is
    handled by HR/policy rather than MarketingConsent, so this helper is used
    only when we explicitly require a MarketingConsent row.
    """
    consent = MarketingConsent.query.filter_by(
        org_id=org_id,
        subject_type=subject_type,
        subject_id=subject_id,
    ).first()
    if not consent:
        return False
    # The model exposes a dedicated location flag.
    return bool(getattr(consent, "location_opt_in", False))


def _current_user_roles() -> List[str]:
    roles = getattr(current_user, "roles", None)
    # Some deployments use a single "role" string instead of a list.
    if isinstance(roles, str):
        return [roles.lower()]
    if roles is None:
        # Fallback to attribute used in older models.
        single = getattr(current_user, "role", None)
        return [single.lower()] if isinstance(single, str) else []
    return [str(r).lower() for r in roles]


# ---------------------------------------------------------------------------
# Ping ingestion
# ---------------------------------------------------------------------------

@bp.post("/ping")
@require_login
def ping() -> Any:
    """Ingest a location ping and update last-known location.

    Behaviour:
    - Accepts pings for the current user.
    - Only privileged roles (dispatch / maintenance / admin) may submit
      pings on behalf of other subjects.
    - For *non* sales/marketing users, honours MarketingConsent.location_opt_in
      when subject_type == "user".
    """
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    subject_type = (payload.get("subject_type") or "").strip()
    subject_id = payload.get("subject_id")
    lat = payload.get("lat")
    lng = payload.get("lng")
    accuracy_m = payload.get("accuracy_m")
    speed_mps = payload.get("speed_mps")
    heading_deg = payload.get("heading_deg")
    label = payload.get("label") or payload.get("site_label")
    source = (payload.get("source") or "app").strip() or "app"

    if not subject_type or subject_id is None or lat is None or lng is None:
        return (
            jsonify({"error": "subject_type, subject_id, lat, lng required"}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        subject_id_int = int(subject_id)
    except (TypeError, ValueError):
        return jsonify({"error": "subject_id must be an integer"}), HTTPStatus.BAD_REQUEST

    # Only allow self-updates unless privileged roles are present.
    user_id = getattr(current_user, "id", None)
    roles = set(_current_user_roles())
    privileged_impersonators = {"dispatch", "maintenance", "admin"}
    if subject_type == "user" and subject_id_int != user_id:
        if roles.isdisjoint(privileged_impersonators):
            return jsonify({"error": "forbidden"}), HTTPStatus.FORBIDDEN

    # Determine whether to enforce MarketingConsent.location_opt_in
    enforce_consent = True
    if subject_type == "user" and subject_id_int == user_id:
        # Field sales & marketing staff are required by policy to share location,
        # so we treat this as operational tracking, not marketing consent.
        if roles.intersection({"sales", "marketing"}):
            enforce_consent = False

    if enforce_consent and not _has_location_consent(org_id, subject_type, subject_id_int):
        # Silently ignore (returns 204 so callers can treat it as "no-op").
        return (
            jsonify(
                {
                    "status": "ignored",
                    "reason": "no_location_consent",
                }
            ),
            HTTPStatus.NO_CONTENT,
        )

    # Persist immutable ping.
    ping = GeoPing(
        org_id=org_id,
        subject_type=subject_type,
        subject_id=subject_id_int,
        lat=float(lat),
        lng=float(lng),
        source=source,
    )
    if hasattr(ping, "accuracy_m") and accuracy_m is not None:
        ping.accuracy_m = accuracy_m
    if hasattr(ping, "speed_mps") and speed_mps is not None:
        ping.speed_mps = speed_mps
    if hasattr(ping, "heading_deg") and heading_deg is not None:
        ping.heading_deg = heading_deg

    db.session.add(ping)

    # Update or create last-known location cache.
    last = GeoLastLocation.query.filter_by(
        org_id=org_id,
        subject_type=subject_type,
        subject_id=subject_id_int,
    ).first()
    if last is None:
        last = GeoLastLocation(
            org_id=org_id,
            subject_type=subject_type,
            subject_id=subject_id_int,
            lat=float(lat),
            lng=float(lng),
        )
        db.session.add(last)
    else:
        last.lat = float(lat)
        last.lng = float(lng)

    if hasattr(last, "accuracy_m") and accuracy_m is not None:
        last.accuracy_m = accuracy_m
    if hasattr(last, "speed_mps") and speed_mps is not None:
        last.speed_mps = speed_mps
    if hasattr(last, "heading_deg") and heading_deg is not None:
        last.heading_deg = heading_deg
    if hasattr(last, "site_label") and label:
        # Some schemas use site_label for human-readable place.
        setattr(last, "site_label", label)

    db.session.commit()

    log_audit(
        user_id=user_id,
        org_id=org_id,
        action="geo.ping",
        details=f"subject={subject_type}#{subject_id_int};source={source}",
        entity_type=subject_type,
        entity_id=subject_id_int,
    )

    return jsonify(_serialize_last_location(last)), HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# Live locations & ETA
# ---------------------------------------------------------------------------

@bp.get("/live")
@require_roles("dispatch", "maintenance", "sales", "marketing", "admin")
def live_locations() -> Any:
    """Return last-known locations for subjects in the current organisation."""
    org_id = resolve_org_id()
    subject_type = (request.args.get("subject_type") or "").strip() or None
    subject_id = request.args.get("subject_id")

    query = GeoLastLocation.query.filter_by(org_id=org_id)
    if subject_type:
        query = query.filter_by(subject_type=subject_type)
    if subject_id:
        try:
            subject_id_int = int(subject_id)
            query = query.filter_by(subject_id=subject_id_int)
        except ValueError:
            return jsonify({"error": "subject_id must be an integer"}), HTTPStatus.BAD_REQUEST

    locations = query.order_by(GeoLastLocation.updated_at.desc()).limit(500).all()
    return jsonify([_serialize_last_location(loc) for loc in locations]), HTTPStatus.OK


@bp.get("/eta")
@require_roles("dispatch", "maintenance", "sales", "marketing", "admin")
def eta() -> Any:
    """Estimate ETA and distance for a subject relative to an assignment or dest.

    Query params:
    - subject_type
    - subject_id
    - dest_lat (optional if assignment exists)
    - dest_lng (optional if assignment exists)
    """
    org_id = resolve_org_id()
    subject_type = (request.args.get("subject_type") or "").strip()
    subject_id = request.args.get("subject_id")

    if not subject_type or subject_id is None:
        return (
            jsonify({"error": "subject_type and subject_id required"}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        subject_id_int = int(subject_id)
    except ValueError:
        return jsonify({"error": "subject_id must be an integer"}), HTTPStatus.BAD_REQUEST

    last = GeoLastLocation.query.filter_by(
        org_id=org_id,
        subject_type=subject_type,
        subject_id=subject_id_int,
    ).first()
    if last is None:
        return jsonify({"error": "no_last_location"}), HTTPStatus.NOT_FOUND

    dest_lat = request.args.get("dest_lat")
    dest_lng = request.args.get("dest_lng")

    assignment = None
    if dest_lat is None or dest_lng is None:
        assignment = (
            GeoAssignment.query.filter_by(
                org_id=org_id,
                subject_type=subject_type,
                subject_id=subject_id_int,
            )
            .order_by(GeoAssignment.started_at.desc())
            .first()
        )
        if assignment and dest_lat is None and getattr(assignment, "dest_lat", None) is not None:
            dest_lat = assignment.dest_lat
        if assignment and dest_lng is None and getattr(assignment, "dest_lng", None) is not None:
            dest_lng = assignment.dest_lng

    if dest_lat is None or dest_lng is None:
        return jsonify({"error": "destination_unknown"}), HTTPStatus.BAD_REQUEST

    distance = haversine_m(last.lat, last.lng, dest_lat, dest_lng)
    # Prefer observed speed if present.
    observed_speed = getattr(last, "speed_mps", None)
    eta_val = eta_seconds(distance, observed_speed)

    response = {
        "subject_type": subject_type,
        "subject_id": subject_id_int,
        "origin": {
            "lat": float(last.lat),
            "lng": float(last.lng),
        },
        "destination": {
            "lat": float(dest_lat),
            "lng": float(dest_lng),
        },
        "distance_m": distance,
        "eta_seconds": eta_val,
    }
    if assignment is not None:
        response["assignment"] = _serialize_assignment(assignment)

    return jsonify(response), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

@bp.post("/assign")
@require_roles("dispatch", "maintenance", "sales", "marketing", "admin")
def assign_task() -> Any:
    """Create or update an assignment for a tracked subject.

    Body:
    - subject_type
    - subject_id
    - task_type (e.g. "maintenance_ticket", "delivery", "visit")
    - task_id
    - dest_lat (optional)
    - dest_lng (optional)
    """
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    subject_type = (payload.get("subject_type") or "").strip()
    subject_id = payload.get("subject_id")
    task_type = (payload.get("task_type") or "").strip()
    task_id = payload.get("task_id")
    dest_lat = payload.get("dest_lat")
    dest_lng = payload.get("dest_lng")

    if not subject_type or subject_id is None or not task_type or task_id is None:
        return (
            jsonify(
                {
                    "error": "subject_type, subject_id, task_type, task_id are required",
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        subject_id_int = int(subject_id)
        task_id_int = int(task_id)
    except (TypeError, ValueError):
        return jsonify({"error": "subject_id and task_id must be integers"}), HTTPStatus.BAD_REQUEST

    assignment = GeoAssignment.query.filter_by(
        org_id=org_id,
        subject_type=subject_type,
        subject_id=subject_id_int,
        task_type=task_type,
        task_id=task_id_int,
    ).first()

    if assignment is None:
        assignment = GeoAssignment(
            org_id=org_id,
            subject_type=subject_type,
            subject_id=subject_id_int,
            task_type=task_type,
            task_id=task_id_int,
        )
        db.session.add(assignment)

    if dest_lat is not None and hasattr(assignment, "dest_lat"):
        assignment.dest_lat = dest_lat
    if dest_lng is not None and hasattr(assignment, "dest_lng"):
        assignment.dest_lng = dest_lng

    # Associate creator if the model exposes created_by_id.
    user_id = getattr(current_user, "id", None)
    if hasattr(assignment, "created_by_id") and assignment.created_by_id is None:
        assignment.created_by_id = user_id

    db.session.commit()

    log_audit(
        user_id=user_id,
        org_id=org_id,
        action="geo.assign",
        details=f"subject={subject_type}#{subject_id_int};task={task_type}#{task_id_int}",
        entity_type=task_type,
        entity_id=task_id_int,
    )

    return jsonify(_serialize_assignment(assignment)), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Route optimisation
# ---------------------------------------------------------------------------

@bp.post("/route/optimize")
@require_roles("dispatch", "maintenance", "sales", "marketing", "admin")
def optimize_route_endpoint() -> Any:
    """Optimize or cache a route and return ETA/distance details.

    Body:
    - origin: {"lat": ..., "lng": ...}
    - dest: {"lat": ..., "lng": ...}
    - waypoints: optional list of {"lat": ..., "lng": ...}
    """
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    origin = payload.get("origin")
    dest = payload.get("dest")
    waypoints = payload.get("waypoints", [])

    if not origin or not dest:
        return jsonify({"error": "origin and dest required"}), HTTPStatus.BAD_REQUEST

    route = optimize_route(org_id, origin, dest, waypoints)
    return jsonify(route), HTTPStatus.OK


__all__ = [
    "bp",
    "ping",
    "live_locations",
    "eta",
    "assign_task",
    "optimize_route_endpoint",
]
