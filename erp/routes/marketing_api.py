from __future__ import annotations

from datetime import date
from decimal import Decimal
from http import HTTPStatus
from typing import Any

from flask import Blueprint, Response, jsonify, request
from flask_login import current_user
from sqlalchemy import func

from erp.extensions import db
from erp.models import MarketingCampaign, MarketingConsent, MarketingEvent, MarketingSegment
from erp.security import require_roles
from erp.utils import resolve_org_id

bp = Blueprint("marketing_api", __name__, url_prefix="/api/marketing")


def _parse_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Campaign CRUD
# ---------------------------------------------------------------------------


def _serialize_campaign(campaign: MarketingCampaign) -> dict[str, Any]:
    return {
        "id": campaign.id,
        "name": campaign.name,
        "description": campaign.description,
        "status": campaign.status,
        "channel": campaign.channel,
        "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
        "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
        "budget": float(campaign.budget or 0),
        "currency": campaign.currency,
        "ab_test_enabled": campaign.ab_test_enabled,
        "created_at": campaign.created_at.isoformat(),
    }


@bp.get("/campaigns")
@require_roles("marketing", "admin")
def list_campaigns():
    org_id = resolve_org_id()
    query = MarketingCampaign.query.filter_by(org_id=org_id).order_by(
        MarketingCampaign.created_at.desc()
    )
    return jsonify([_serialize_campaign(c) for c in query.all()]), HTTPStatus.OK


@bp.post("/campaigns")
@require_roles("marketing", "admin")
def create_campaign():
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), HTTPStatus.BAD_REQUEST

    campaign = MarketingCampaign(
        org_id=org_id,
        name=name,
        description=(payload.get("description") or "").strip() or None,
        status=(payload.get("status") or "draft").lower(),
        channel=(payload.get("channel") or "telegram").lower(),
        start_date=date.fromisoformat(payload["start_date"]) if payload.get("start_date") else None,
        end_date=date.fromisoformat(payload["end_date"]) if payload.get("end_date") else None,
        budget=_parse_decimal(payload.get("budget")),
        currency=(payload.get("currency") or "ETB").upper(),
        ab_test_enabled=bool(payload.get("ab_test_enabled", False)),
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(campaign)
    db.session.commit()
    return jsonify(_serialize_campaign(campaign)), HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------


def _serialize_segment(segment: MarketingSegment) -> dict[str, Any]:
    return {
        "id": segment.id,
        "campaign_id": segment.campaign_id,
        "name": segment.name,
        "rules": segment.rules_json,
        "is_active": segment.is_active,
        "created_at": segment.created_at.isoformat(),
    }


@bp.post("/campaigns/<int:campaign_id>/segments")
@require_roles("marketing", "admin")
def create_segment(campaign_id: int):
    org_id = resolve_org_id()
    campaign = MarketingCampaign.query.filter_by(org_id=org_id, id=campaign_id).first_or_404()

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "segment name required"}), HTTPStatus.BAD_REQUEST

    rules = payload.get("rules") or {}
    segment = MarketingSegment(
        org_id=org_id,
        campaign_id=campaign.id,
        name=name,
        rules_json=rules,
        is_active=True,
        created_by_id=getattr(current_user, "id", None),
    )
    db.session.add(segment)
    db.session.commit()
    return jsonify(_serialize_segment(segment)), HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# Consent
# ---------------------------------------------------------------------------


def _serialize_consent(consent: MarketingConsent) -> dict[str, Any]:
    return {
        "id": consent.id,
        "subject_type": consent.subject_type,
        "subject_id": consent.subject_id,
        "marketing_opt_in": consent.marketing_opt_in,
        "location_opt_in": consent.location_opt_in,
        "consent_source": consent.consent_source,
        "consent_version": consent.consent_version,
        "updated_at": consent.updated_at.isoformat(),
    }


@bp.post("/consent")
def upsert_consent():
    """Store opt-in/opt-out preferences for marketing and location use."""
    org_id = resolve_org_id()
    payload = request.get_json(silent=True) or {}

    subject_type = (payload.get("subject_type") or "").strip()
    subject_id = payload.get("subject_id")
    if not (subject_type and subject_id):
        return jsonify({"error": "subject_type and subject_id required"}), HTTPStatus.BAD_REQUEST

    existing = MarketingConsent.query.filter_by(
        org_id=org_id, subject_type=subject_type, subject_id=subject_id
    ).first()

    if existing:
        existing.marketing_opt_in = bool(payload.get("marketing_opt_in", existing.marketing_opt_in))
        existing.location_opt_in = bool(payload.get("location_opt_in", existing.location_opt_in))
        existing.consent_source = (payload.get("consent_source") or existing.consent_source)
        existing.consent_version = (payload.get("consent_version") or existing.consent_version)
        existing.updated_by_id = getattr(current_user, "id", None)
        db.session.commit()
        return jsonify(_serialize_consent(existing)), HTTPStatus.OK

    consent = MarketingConsent(
        org_id=org_id,
        subject_type=subject_type,
        subject_id=subject_id,
        marketing_opt_in=bool(payload.get("marketing_opt_in", False)),
        location_opt_in=bool(payload.get("location_opt_in", False)),
        consent_source=(payload.get("consent_source") or "unknown"),
        consent_version=(payload.get("consent_version") or "v1"),
        updated_by_id=getattr(current_user, "id", None),
    )
    db.session.add(consent)
    db.session.commit()
    return jsonify(_serialize_consent(consent)), HTTPStatus.CREATED


# ---------------------------------------------------------------------------
# Campaign stats + SSE stream
# ---------------------------------------------------------------------------


def _campaign_stats(org_id: int, campaign_id: int) -> dict[str, int]:
    query = (
        db.session.query(MarketingEvent.event_type, func.count(MarketingEvent.id))
        .filter(MarketingEvent.org_id == org_id, MarketingEvent.campaign_id == campaign_id)
        .group_by(MarketingEvent.event_type)
    )
    return {etype: int(count) for etype, count in query.all()}


@bp.get("/campaigns/<int:campaign_id>/stats")
@require_roles("marketing", "admin")
def campaign_stats(campaign_id: int):
    org_id = resolve_org_id()
    counts = _campaign_stats(org_id, campaign_id)
    return jsonify(counts), HTTPStatus.OK


@bp.get("/campaigns/<int:campaign_id>/stats/stream")
@require_roles("marketing", "admin")
def stream_campaign_stats(campaign_id: int):
    org_id = resolve_org_id()
    interval = int(request.args.get("interval", "5"))

    def gen():
        while True:
            counts = _campaign_stats(org_id, campaign_id)
            yield f"data: {counts}\n\n"
            import time

            time.sleep(interval)

    return Response(gen(), mimetype="text/event-stream")


__all__ = [
    "bp",
    "list_campaigns",
    "create_campaign",
    "create_segment",
    "upsert_consent",
    "campaign_stats",
    "stream_campaign_stats",
]
