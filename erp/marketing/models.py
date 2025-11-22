from __future__ import annotations

from datetime import UTC, datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    visited_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)


class MarketingCampaign(TimestampMixin, OrgScopedMixin, db.Model):
    __tablename__ = "marketing_campaigns"
    __table_args__ = (
        Index("ix_marketing_campaigns_org", "org_id"),
        Index("ix_marketing_campaigns_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text)
    status: Mapped[str] = mapped_column(db.String(32), nullable=False, default="draft")
    channel: Mapped[str] = mapped_column(db.String(32), nullable=False, default="telegram")
    start_date: Mapped[Optional[date]] = mapped_column(db.Date)
    end_date: Mapped[Optional[date]] = mapped_column(db.Date)
    budget: Mapped[Optional[Decimal]] = mapped_column(db.Numeric(14, 2))
    currency: Mapped[str] = mapped_column(db.String(8), nullable=False, default="ETB")
    ab_test_enabled: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(db.Integer)

    segments = relationship(
        "MarketingSegment",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="MarketingSegment.id",
    )
    variants = relationship(
        "MarketingABVariant",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="MarketingABVariant.id",
    )
    geofences = relationship(
        "MarketingGeofence",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="MarketingGeofence.id",
    )
    events = relationship(
        "MarketingEvent",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="MarketingEvent.created_at",
    )


class MarketingSegment(TimestampMixin, OrgScopedMixin, db.Model):
    __tablename__ = "marketing_segments"
    __table_args__ = (
        Index("ix_marketing_segments_org", "org_id"),
        Index("ix_marketing_segments_campaign", "campaign_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("marketing_campaigns.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    rules_json: Mapped[dict] = mapped_column(db.JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(db.Integer)

    campaign = relationship("MarketingCampaign", back_populates="segments")


class MarketingConsent(TimestampMixin, OrgScopedMixin, db.Model):
    __tablename__ = "marketing_consents"
    __table_args__ = (Index("ix_marketing_consents_subject", "subject_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_type: Mapped[str] = mapped_column(db.String(32), nullable=False)
    subject_id: Mapped[int] = mapped_column(db.Integer, nullable=False)
    marketing_opt_in: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    location_opt_in: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    consent_source: Mapped[Optional[str]] = mapped_column(db.String(64))
    consent_version: Mapped[Optional[str]] = mapped_column(db.String(32))
    updated_by_id: Mapped[Optional[int]] = mapped_column(db.Integer)


class MarketingABVariant(TimestampMixin, OrgScopedMixin, db.Model):
    __tablename__ = "marketing_ab_variants"
    __table_args__ = (
        Index("ix_marketing_ab_variants_org", "org_id"),
        Index("ix_marketing_ab_variants_campaign", "campaign_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("marketing_campaigns.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(db.String(64), nullable=False)
    weight: Mapped[Decimal] = mapped_column(db.Numeric(5, 2), nullable=False, default=Decimal("50.00"))
    template_json: Mapped[dict] = mapped_column(db.JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(db.Integer)

    campaign = relationship("MarketingCampaign", back_populates="variants")


class MarketingGeofence(TimestampMixin, OrgScopedMixin, db.Model):
    __tablename__ = "marketing_geofences"
    __table_args__ = (
        Index("ix_marketing_geofences_org", "org_id"),
        Index("ix_marketing_geofences_campaign", "campaign_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("marketing_campaigns.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    center_lat: Mapped[Decimal] = mapped_column(db.Numeric(10, 6), nullable=False)
    center_lng: Mapped[Decimal] = mapped_column(db.Numeric(10, 6), nullable=False)
    radius_meters: Mapped[int] = mapped_column(db.Integer, nullable=False, default=200)
    action_type: Mapped[str] = mapped_column(db.String(32), nullable=False, default="notify")
    action_payload: Mapped[dict] = mapped_column(db.JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(db.Integer)

    campaign = relationship("MarketingCampaign", back_populates="geofences")


class MarketingEvent(TimestampMixin, OrgScopedMixin, db.Model):
    __tablename__ = "marketing_events"
    __table_args__ = (
        Index("ix_marketing_events_org", "org_id"),
        Index("ix_marketing_events_campaign", "campaign_id"),
        Index("ix_marketing_events_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("marketing_campaigns.id", ondelete="CASCADE"), nullable=True
    )
    # Legacy event fields retained for compatibility with existing UI endpoints
    title: Mapped[Optional[str]] = mapped_column(db.String(255))
    event_type: Mapped[str] = mapped_column(db.String(64), nullable=False, default="workshop")
    venue: Mapped[Optional[str]] = mapped_column(db.String(255))
    start_date: Mapped[Optional[date]] = mapped_column(db.Date)
    end_date: Mapped[Optional[date]] = mapped_column(db.Date)
    status: Mapped[str] = mapped_column(db.String(32), nullable=False, default="planned")

    # Engagement/event stream fields
    subject_type: Mapped[Optional[str]] = mapped_column(db.String(32))
    subject_id: Mapped[Optional[int]] = mapped_column(db.Integer, index=True)
    metadata_json: Mapped[dict] = mapped_column(db.JSON, nullable=False, default=dict)

    campaign = relationship("MarketingCampaign", back_populates="events")


__all__ = [
    "MarketingVisit",
    "MarketingCampaign",
    "MarketingSegment",
    "MarketingConsent",
    "MarketingABVariant",
    "MarketingGeofence",
    "MarketingEvent",
]
