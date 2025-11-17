from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from erp.models import db
from erp.models.core_entities import OrgScopedMixin, TimestampMixin


class MarketingVisit(TimestampMixin, OrgScopedMixin, db.Model):
    __tablename__ = "marketing_visits"
    __table_args__ = (
        Index("ix_marketing_visits_org", "org_id"),
        Index("ix_marketing_visits_institution", "institution"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    institution: Mapped[str] = mapped_column(db.String(255), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(db.String(255))
    rep_name: Mapped[str | None] = mapped_column(db.String(255))
    lat: Mapped[float] = mapped_column(db.Float, nullable=False)
    lng: Mapped[float] = mapped_column(db.Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(db.Text)
    visited_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)


class MarketingEvent(TimestampMixin, OrgScopedMixin, db.Model):
    __tablename__ = "marketing_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(db.String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(db.String(50), nullable=False, default="workshop")
    venue: Mapped[str | None] = mapped_column(db.String(255))
    start_date: Mapped[date | None] = mapped_column(db.Date)
    end_date: Mapped[date | None] = mapped_column(db.Date)
    status: Mapped[str] = mapped_column(db.String(32), nullable=False, default="planned")


__all__ = ["MarketingVisit", "MarketingEvent"]
