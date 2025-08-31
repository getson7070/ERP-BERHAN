"""Inventory domain models and tasks for lot and serial tracking."""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy.sql import func

from ..extensions import db
from .. import celery


class Lot(db.Model):  # type: ignore[name-defined]
    __tablename__ = "inventory_lots"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    item_id = db.Column(
        db.Integer, db.ForeignKey("inventory_items.id"), nullable=False, index=True
    )
    lot_number = db.Column(db.String(64), nullable=False, unique=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    expiry_date = db.Column(db.Date, index=True)


class Serial(db.Model):  # type: ignore[name-defined]
    __tablename__ = "inventory_serials"

    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(
        db.Integer, db.ForeignKey("inventory_lots.id"), nullable=False, index=True
    )
    serial_number = db.Column(db.String(128), nullable=False, unique=True)


class Potency(db.Model):  # type: ignore[name-defined]
    __tablename__ = "inventory_potencies"

    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(
        db.Integer, db.ForeignKey("inventory_lots.id"), nullable=False, index=True
    )
    value = db.Column(db.Float, nullable=False)
    tested_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


@celery.task
def assign_lot(item_id: int, quantity: int) -> str:
    """Assign a lot number to a batch of items."""
    lot = Lot(
        org_id=0,
        item_id=item_id,
        lot_number=f"LOT-{datetime.utcnow().timestamp():.0f}",
        quantity=quantity,
        expiry_date=datetime.utcnow() + timedelta(days=365),
    )
    db.session.add(lot)
    db.session.commit()
    current_app.logger.info("assigned lot %s", lot.lot_number)
    return lot.lot_number


@celery.task
def check_expiry() -> int:
    """Return count of lots nearing expiry within 30 days."""
    threshold = datetime.utcnow() + timedelta(days=30)
    return Lot.query.filter(Lot.expiry_date <= threshold).count()
