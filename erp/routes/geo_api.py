"""Geolocation APIs for live tracking, ETA, and assignments."""
from __future__ import annotations

from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.models import GeoAssignment, GeoLastLocation, GeoPing, MarketingConsent
from erp.security import require_login, require_roles
from erp.services.geo_utils import eta_seconds, haversine_m
from erp.services.route_opt import optimize_route
from erp.utils import resolve_org_id

bp = Blueprint("geo_api", __name__, url_prefix="/api/geo")


def _serialize_last(last: GeoLastLocation) -> dict[str, Any]:
    return {
        "subject_type": last.subject_type,
        "subject_id": last.subject_id,
        "lat": float(last.lat),
        "lng": float(last.lng),
        "accuracy_m": last.accuracy_m,
        "speed_mps": float(last.speed_mps or 0),
        "heading_deg": float(last.heading_deg or 0),
        "updated_at": last.updated_at.isoformat(),
    }


@bp.post("/ping")
@require_login
def record_ping():
    """Ingest a raw location ping and update the last-known cache."""

    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    subject_type = payload.get("subject_type")
    subject_id = payload.get("subject_id")
    lat = payload.get("lat")
    lng = payload.get("lng")

    if not (subject_type and subject_id and lat and lng):
        return jsonify({"error": "subject_type, subject_id, lat, lng required"}), HTTPStatus.BAD_REQUEST

    # Only allow self-updates unless privileged roles are present.
    allowed_roles = {"dispatch", "maintenance", "admin"}
    user_roles = {r.lower() for r in getattr(current_user, "roles", []) or []}
    if subject_type == "user" and subject_id != getattr(current_user, "id", None):
        if allowed_roles.isdisjoint(user_roles):
            return jsonify({"error": "forbidden"}), HTTPStatus.FORBIDDEN

    consent = MarketingConsent.query.filter_by(org_id=org_id, subject_type=subject_type, subject_id=subject_id).first()
    if consent and not consent.location_opt_in:
        return jsonify({"status": "ignored_no_consent"}), HTTPStatus.OK

    ping = GeoPing(
        org_id=org_id,
        subject_type=subject_type,
        subject_id=subject_id,
        lat=lat,
        lng=lng,
        accuracy_m=payload.get("accuracy_m"),
        speed_mps=payload.get("speed_mps"),
        heading_deg=payload.get("heading_deg"),
        source=payload.get("source") or "app",
    )
    db.session.add(ping)

    last = GeoLastLocation.query.filter_by(
        org_id=org_id, subject_type=subject_type, subject_id=subject_id
    ).first()
    if last:
        last.lat = lat
        last.lng = lng
        last.accuracy_m = payload.get("accuracy_m")
        last.speed_mps = payload.get("speed_mps")
        last.heading_deg = payload.get("heading_deg")
    else:
        last = GeoLastLocation(
            org_id=org_id,
            subject_type=subject_type,
            subject_id=subject_id,
            lat=lat,
            lng=lng,
            accuracy_m=payload.get("accuracy_m"),
            speed_mps=payload.get("speed_mps"),
            heading_deg=payload.get("heading_deg"),
        )
        db.session.add(last)

    db.session.commit()
    return jsonify({"status": "ok"}), HTTPStatus.CREATED


@bp.get("/live")
@require_roles("dispatch", "maintenance", "admin")
def live_locations():
    """Return last-known locations for active assignments or all tracked subjects."""

    org_id = resolve_org_id()
    task_type = request.args.get("task_type")
    task_id = request.args.get("task_id")

    if task_type and task_id:
        assignments = GeoAssignment.query.filter_by(
            org_id=org_id, task_type=task_type, task_id=task_id, status="active"
        ).all()
        allowed = {(a.subject_type, a.subject_id) for a in assignments}
        candidates = GeoLastLocation.query.filter_by(org_id=org_id).all()
        records = [loc for loc in candidates if (loc.subject_type, loc.subject_id) in allowed]
    else:
        records = GeoLastLocation.query.filter_by(org_id=org_id).all()

    return jsonify([_serialize_last(loc) for loc in records]), HTTPStatus.OK


@bp.post("/assign")
@require_roles("dispatch", "maintenance", "admin")
def assign_subject():
    """Assign a driver/technician to a task with optional destination for ETA."""

    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    assignment = GeoAssignment(
        org_id=org_id,
        subject_type=payload["subject_type"],
        subject_id=payload["subject_id"],
        task_type=payload["task_type"],
        task_id=payload["task_id"],
        dest_lat=payload.get("dest_lat"),
        dest_lng=payload.get("dest_lng"),
        status="active",
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"id": assignment.id}), HTTPStatus.CREATED


@bp.get("/eta")
@require_roles("dispatch", "maintenance", "admin")
def eta_for_subject():
    """Compute ETA from last known location to destination or active assignment."""

    org_id = resolve_org_id()
    subject_type = request.args.get("subject_type")
    subject_id = request.args.get("subject_id")
    dest_lat = request.args.get("dest_lat")
    dest_lng = request.args.get("dest_lng")

    if not (subject_type and subject_id):
        return jsonify({"error": "subject_type and subject_id required"}), HTTPStatus.BAD_REQUEST

    last = GeoLastLocation.query.filter_by(org_id=org_id, subject_type=subject_type, subject_id=subject_id).first()
    if not last:
        return jsonify({"error": "no location"}), HTTPStatus.NOT_FOUND

    if not (dest_lat and dest_lng):
        assignment = GeoAssignment.query.filter_by(
            org_id=org_id,
            subject_type=subject_type,
            subject_id=subject_id,
            status="active",
        ).order_by(GeoAssignment.started_at.desc()).first()
        if assignment:
            dest_lat = assignment.dest_lat
            dest_lng = assignment.dest_lng

    if not (dest_lat and dest_lng):
        return jsonify({"error": "destination required"}), HTTPStatus.BAD_REQUEST

    distance = haversine_m(last.lat, last.lng, dest_lat, dest_lng)
    eta_value = eta_seconds(distance, last.speed_mps)

    return jsonify({
        "distance_m": distance,
        "eta_seconds": eta_value,
        "eta_minutes": int(eta_value / 60),
    }), HTTPStatus.OK


@bp.post("/route/optimize")
@require_roles("dispatch", "maintenance", "admin")
def optimize_route_endpoint():
    """Optimize or cache a route and return ETA/distance details."""

    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}
    origin = payload.get("origin")
    dest = payload.get("dest")
    waypoints = payload.get("waypoints", [])

    if not (origin and dest):
        return jsonify({"error": "origin and dest required"}), HTTPStatus.BAD_REQUEST

    route = optimize_route(org_id, origin, dest, waypoints)
    return jsonify(route), HTTPStatus.OK
