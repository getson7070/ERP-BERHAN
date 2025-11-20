from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus
from math import asin, cos, radians, sin, sqrt
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user

from erp.extensions import db
from erp.models import MarketingCampaign, MarketingConsent, MarketingEvent, MarketingGeofence
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("marketing_geofence", __name__, url_prefix="/api/marketing/geofence")


def _haversine_m(lat1: float, lng1: float, lat2: Decimal, lng2: Decimal) -> float:
    radius = 6_371_000.0
    lat1_r, lng1_r, lat2_r, lng2_r = map(radians, [float(lat1), float(lng1), float(lat2), float(lng2)])
    dlat = lat2_r - lat1_r
    dlng = lng2_r - lng1_r
    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlng / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radius * c


def _serialize_geofence(geofence: MarketingGeofence) -> dict[str, Any]:
    return {
        "id": geofence.id,
        "campaign_id": geofence.campaign_id,
        "name": geofence.name,
        "center_lat": float(geofence.center_lat),
        "center_lng": float(geofence.center_lng),
        "radius_meters": geofence.radius_meters,
        "action_type": geofence.action_type,
        "action_payload": geofence.action_payload,
        "is_active": geofence.is_active,
    }


@bp.post("/campaigns/<int:campaign_id>")
@require_roles("marketing", "admin")
def create_geofence(campaign_id: int):
    org_id = resolve_org_id()
    campaign = MarketingCampaign.query.filter_by(org_id=org_id, id=campaign_id).first_or_404()
    payload = request.get_json(silent=True) or {}

    geofence = MarketingGeofence(
        org_id=org_id,
        campaign_id=campaign.id,
        name=(payload.get("name") or "Geofence").strip(),
        center_lat=Decimal(str(payload["center_lat"])),
        center_lng=Decimal(str(payload["center_lng"])),
        radius_meters=int(payload.get("radius_meters", 200)),
        action_type=(payload.get("action_type") or "notify").lower(),
        action_payload=payload.get("action_payload") or {},
        is_active=True,
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(geofence)
    db.session.commit()
    return jsonify(_serialize_geofence(geofence)), HTTPStatus.CREATED


@bp.post("/trigger")
def trigger_geofence():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    subject_type = payload.get("subject_type")
    subject_id = payload.get("subject_id")
    lat = payload.get("lat")
    lng = payload.get("lng")

    if not (subject_type and subject_id and lat is not None and lng is not None):
        return jsonify({"error": "subject_type, subject_id, lat, lng required"}), HTTPStatus.BAD_REQUEST

    consent = MarketingConsent.query.filter_by(
        org_id=org_id, subject_type=subject_type, subject_id=subject_id
    ).first()
    if consent and not consent.location_opt_in:
        return jsonify({"status": "ignored_no_location_consent"}), HTTPStatus.OK

    geofences = MarketingGeofence.query.filter_by(org_id=org_id, is_active=True).all()
    triggered: list[dict[str, Any]] = []

    for geofence in geofences:
        distance_m = _haversine_m(float(lat), float(lng), geofence.center_lat, geofence.center_lng)
        if distance_m <= geofence.radius_meters:
            event = MarketingEvent(
                org_id=org_id,
                campaign_id=geofence.campaign_id,
                subject_type=subject_type,
                subject_id=subject_id,
                event_type="geofence_triggered",
                metadata_json={
                    "geofence_id": geofence.id,
                    "distance_m": distance_m,
                    "action_type": geofence.action_type,
                },
            )
            db.session.add(event)
            triggered.append({"geofence_id": geofence.id, "campaign_id": geofence.campaign_id})

    db.session.commit()
    return jsonify({"triggered": triggered}), HTTPStatus.OK


__all__ = ["bp", "create_geofence", "trigger_geofence"]
