"""Geolocation models for live tracking, assignments, and route caching."""
from __future__ import annotations

from sqlalchemy import UniqueConstraint, func, Index

from erp.extensions import db


class GeoPing(db.Model):
    """Immutable record of a location ping for auditing and history."""

    __tablename__ = "geo_pings"
    __table_args__ = (
        Index("ix_geo_pings_subject_time", "org_id", "subject_type", "subject_id", "recorded_at"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    subject_type = db.Column(db.String(32), nullable=False, index=True)
    subject_id = db.Column(db.Integer, nullable=False, index=True)

    lat = db.Column(db.Numeric(10, 6), nullable=False)
    lng = db.Column(db.Numeric(10, 6), nullable=False)
    accuracy_m = db.Column(db.Integer, nullable=True)

    speed_mps = db.Column(db.Numeric(10, 3), nullable=True)
    heading_deg = db.Column(db.Numeric(6, 2), nullable=True)

    source = db.Column(db.String(32), nullable=False, default="app")

    recorded_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class GeoLastLocation(db.Model):
    """Cache of the last known location for fast map rendering."""

    __tablename__ = "geo_last_locations"
    __table_args__ = (
        UniqueConstraint("org_id", "subject_type", "subject_id", name="uq_geo_last"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    subject_type = db.Column(db.String(32), nullable=False, index=True)
    subject_id = db.Column(db.Integer, nullable=False, index=True)

    lat = db.Column(db.Numeric(10, 6), nullable=False)
    lng = db.Column(db.Numeric(10, 6), nullable=False)
    accuracy_m = db.Column(db.Integer, nullable=True)

    speed_mps = db.Column(db.Numeric(10, 3), nullable=True)
    heading_deg = db.Column(db.Numeric(6, 2), nullable=True)

    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class GeoAssignment(db.Model):
    """Active task assignment (delivery, maintenance, visit) for a tracked subject."""

    __tablename__ = "geo_assignments"
    __table_args__ = (
        Index("ix_geo_assign_task", "org_id", "task_type", "task_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    subject_type = db.Column(db.String(32), nullable=False)
    subject_id = db.Column(db.Integer, nullable=False, index=True)

    task_type = db.Column(db.String(32), nullable=False, index=True)
    task_id = db.Column(db.Integer, nullable=False, index=True)

    status = db.Column(db.String(32), nullable=False, default="active", index=True)

    started_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    completed_at = db.Column(db.DateTime, nullable=True)

    dest_lat = db.Column(db.Numeric(10, 6), nullable=True)
    dest_lng = db.Column(db.Numeric(10, 6), nullable=True)

    created_by_id = db.Column(db.Integer, nullable=True)


class GeoRouteCache(db.Model):
    """Cached route calculations (internal fallback or third-party providers)."""

    __tablename__ = "geo_route_cache"
    __table_args__ = (UniqueConstraint("org_id", "cache_key", name="uq_route_cache"),)

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    cache_key = db.Column(db.String(128), nullable=False, index=True)
    provider = db.Column(db.String(32), nullable=False, default="internal")
    route_json = db.Column(db.JSON, nullable=False, default=dict)

    eta_seconds = db.Column(db.Integer, nullable=True)
    distance_meters = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
