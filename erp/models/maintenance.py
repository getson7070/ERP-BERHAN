"""Maintenance and asset management domain models."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from erp.extensions import db


class MaintenanceAsset(db.Model):
    """Physical asset under maintenance control."""

    __tablename__ = "maintenance_assets"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    code = db.Column(db.String(64), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64), nullable=True)
    manufacturer = db.Column(db.String(128), nullable=True)
    model = db.Column(db.String(128), nullable=True)
    serial_number = db.Column(db.String(128), nullable=True, index=True)
    location = db.Column(db.String(255), nullable=True)

    purchase_date = db.Column(db.Date, nullable=True)
    purchase_cost = db.Column(db.Numeric(14, 2), nullable=True)
    salvage_value = db.Column(db.Numeric(14, 2), nullable=True)
    useful_life_years = db.Column(db.Integer, nullable=True)
    depreciation_method = db.Column(db.String(32), nullable=False, default="straight_line")

    is_critical = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_by_id = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    schedules = db.relationship(
        "MaintenanceSchedule",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="MaintenanceSchedule.id",
    )
    work_orders = db.relationship(
        "MaintenanceWorkOrder",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="MaintenanceWorkOrder.id",
    )
    sensor_readings = db.relationship(
        "MaintenanceSensorReading",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="MaintenanceSensorReading.recorded_at.desc()",
    )


class MaintenanceSchedule(db.Model):
    """Preventive maintenance schedule for an asset."""

    __tablename__ = "maintenance_schedules"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = db.Column(db.String(255), nullable=False)
    schedule_type = db.Column(db.String(32), nullable=False, default="time")

    interval_days = db.Column(db.Integer, nullable=True)
    next_due_date = db.Column(db.Date, nullable=True)
    last_completed_date = db.Column(db.Date, nullable=True)

    usage_metric = db.Column(db.String(64), nullable=True)
    usage_interval = db.Column(db.Integer, nullable=True)
    last_usage_value = db.Column(db.Numeric(14, 2), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_by_id = db.Column(db.Integer, nullable=True)

    asset = db.relationship("MaintenanceAsset", back_populates="schedules")


class MaintenanceWorkOrder(db.Model):
    """Maintenance job (preventive or corrective) with downtime and cost tracking."""

    __tablename__ = "maintenance_work_orders"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    schedule_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_schedules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    work_type = db.Column(db.String(32), nullable=False, default="corrective")

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(32), nullable=False, default="open", index=True)
    priority = db.Column(db.String(32), nullable=False, default="normal")

    requested_by_id = db.Column(db.Integer, nullable=True)
    assigned_to_id = db.Column(db.Integer, nullable=True)

    request_lat = db.Column(db.Float, nullable=True)
    request_lng = db.Column(db.Float, nullable=True)
    request_location_label = db.Column(db.String(255), nullable=True)

    start_lat = db.Column(db.Float, nullable=True)
    start_lng = db.Column(db.Float, nullable=True)
    last_check_in_at = db.Column(db.DateTime(timezone=True), nullable=True)

    requested_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    due_date = db.Column(db.Date, nullable=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    sla_status = db.Column(db.String(32), nullable=False, default="ok")

    downtime_start = db.Column(db.DateTime(timezone=True), nullable=True)
    downtime_end = db.Column(db.DateTime(timezone=True), nullable=True)
    downtime_minutes = db.Column(db.Integer, nullable=True)

    labor_cost = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    material_cost = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    other_cost = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    total_cost = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    asset = db.relationship("MaintenanceAsset", back_populates="work_orders")
    schedule = db.relationship("MaintenanceSchedule")
    events = db.relationship(
        "MaintenanceEvent",
        back_populates="work_order",
        cascade="all, delete-orphan",
        order_by="MaintenanceEvent.created_at.asc()",
    )

    def recompute_total_cost(self) -> None:
        self.total_cost = (self.labor_cost or 0) + (self.material_cost or 0) + (self.other_cost or 0)


class MaintenanceEvent(db.Model):
    """Timeline events for a work order."""

    __tablename__ = "maintenance_events"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    work_order_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = db.Column(db.String(64), nullable=False, index=True)
    message = db.Column(db.Text, nullable=True)
    from_status = db.Column(db.String(32), nullable=True)
    to_status = db.Column(db.String(32), nullable=True)

    geo_lat = db.Column(db.Float, nullable=True)
    geo_lng = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_by_id = db.Column(db.Integer, nullable=True)

    work_order = db.relationship("MaintenanceWorkOrder", back_populates="events")


class MaintenanceEscalationRule(db.Model):
    """Escalation thresholds for critical assets."""

    __tablename__ = "maintenance_escalation_rules"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    name = db.Column(db.String(255), nullable=False)
    asset_category = db.Column(db.String(64), nullable=True)
    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    min_priority = db.Column(db.String(32), nullable=False, default="normal")
    downtime_threshold_minutes = db.Column(db.Integer, nullable=False, default=60)

    notify_role = db.Column(db.String(64), nullable=True)
    notify_channel = db.Column(db.String(32), nullable=False, default="telegram")

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_by_id = db.Column(db.Integer, nullable=True)


class MaintenanceEscalationEvent(db.Model):
    """Record of an escalation trigger for a work order."""

    __tablename__ = "maintenance_escalation_events"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    rule_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_escalation_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    work_order_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_work_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status = db.Column(db.String(32), nullable=False, default="triggered")
    note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_by_id = db.Column(db.Integer, nullable=True)

    rule = db.relationship("MaintenanceEscalationRule")
    work_order = db.relationship("MaintenanceWorkOrder")


class MaintenanceSensorReading(db.Model):
    """Optional IoT/sensor telemetry for an asset."""

    __tablename__ = "maintenance_sensor_readings"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sensor_type = db.Column(db.String(64), nullable=False)
    value = db.Column(db.Numeric(14, 4), nullable=True)
    unit = db.Column(db.String(32), nullable=True)
    raw_payload = db.Column(db.JSON, nullable=True)

    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    asset = db.relationship("MaintenanceAsset", back_populates="sensor_readings")


__all__ = [
    "MaintenanceAsset",
    "MaintenanceSchedule",
    "MaintenanceWorkOrder",
    "MaintenanceEvent",
    "MaintenanceEscalationRule",
    "MaintenanceEscalationEvent",
    "MaintenanceSensorReading",
]
