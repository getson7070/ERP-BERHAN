from __future__ import annotations

from datetime import datetime, date
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_login import login_required

from erp.audit import log_audit
from erp.extensions import db
from erp.utils import resolve_org_id, role_required
from .models import MarketingEvent, MarketingVisit

bp = Blueprint("marketing", __name__, url_prefix="/marketing")


def _serialize_visit(visit: MarketingVisit) -> dict[str, object]:
    return {
        "id": visit.id,
        "org_id": visit.org_id,
        "institution": visit.institution,
        "contact": visit.contact_person,
        "notes": visit.notes,
        "lat": visit.lat,
        "lng": visit.lng,
        "visited_at": visit.visited_at.isoformat(),
        "rep_name": visit.rep_name,
    }


def _serialize_event(event: MarketingEvent) -> dict[str, object]:
    return {
        "id": event.id,
        "title": event.title,
        "event_type": event.event_type,
        "venue": event.venue,
        "start_date": event.start_date.isoformat() if event.start_date else None,
        "end_date": event.end_date.isoformat() if event.end_date else None,
        "status": event.status,
    }


@bp.route("/visits", methods=["GET", "POST"])
@login_required
@role_required("Staff", "Manager", "Admin")
def visits():
    org_id = resolve_org_id()
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        institution = (payload.get("institution") or "").strip()
        rep_name = (payload.get("rep_name") or "").strip()
        if not institution:
            return jsonify({"error": "institution is required"}), HTTPStatus.BAD_REQUEST
        lat = payload.get("lat")
        lng = payload.get("lng")
        if lat is None or lng is None:
            return jsonify({"error": "lat and lng are required"}), HTTPStatus.BAD_REQUEST
        visit = MarketingVisit(
            org_id=org_id,
            institution=institution,
            contact_person=payload.get("contact_person"),
            notes=payload.get("notes"),
            lat=lat,
            lng=lng,
            rep_name=rep_name or None,
            visited_at=payload.get("visited_at") or datetime.utcnow(),
        )
        db.session.add(visit)
        db.session.commit()
        log_audit(None, org_id, "marketing.visit_logged", f"visit={visit.id};inst={institution}")
        return jsonify(_serialize_visit(visit)), HTTPStatus.CREATED

    records = (
        MarketingVisit.query.filter_by(org_id=org_id)
        .order_by(MarketingVisit.visited_at.desc())
        .all()
    )
    return jsonify([_serialize_visit(v) for v in records])


@bp.route("/events", methods=["GET", "POST"])
@login_required
@role_required("Manager", "Admin")
def events():
    org_id = resolve_org_id()
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "").strip()
        event_type = (payload.get("event_type") or "workshop").strip()
        start_date = payload.get("start_date") or date.today()
        end_date = payload.get("end_date") or start_date
        if not title:
            return jsonify({"error": "title is required"}), HTTPStatus.BAD_REQUEST

        event = MarketingEvent(
            org_id=org_id,
            title=title,
            event_type=event_type,
            venue=payload.get("venue"),
            start_date=start_date,
            end_date=end_date,
            status=payload.get("status", "planned"),
        )
        db.session.add(event)
        db.session.commit()
        log_audit(None, org_id, "marketing.event_created", f"event={event.id};type={event_type}")
        return jsonify(_serialize_event(event)), HTTPStatus.CREATED

    events = (
        MarketingEvent.query.filter_by(org_id=org_id)
        .order_by(MarketingEvent.start_date.desc())
        .all()
    )
    return jsonify([_serialize_event(ev) for ev in events])


__all__ = ["bp", "visits", "events"]
