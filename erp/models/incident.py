"""Incident tracking for MTTR calculations."""
from __future__ import annotations

from sqlalchemy import func

from . import db


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    org_id = db.Column(db.Integer, nullable=False, index=True)

    service = db.Column(db.String(64), nullable=False, index=True)

    started_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    recovered_at = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(16), nullable=False, default="open", index=True)

    detail_json = db.Column(db.JSON, nullable=False, default=dict)
