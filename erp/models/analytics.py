"""Analytics registry, facts, dashboards, and lineage models."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import UniqueConstraint, func

from erp.extensions import db


class AnalyticsMetric(db.Model):
    """Registry of metrics available for analytics and dashboards."""

    __tablename__ = "analytics_metrics"
    __table_args__ = (UniqueConstraint("org_id", "key", name="uq_metric_key"),)

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    key = db.Column(db.String(128), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    unit = db.Column(db.String(32), nullable=True)
    metric_type = db.Column(db.String(32), nullable=False, default="gauge")

    privacy_class = db.Column(db.String(32), nullable=False, default="internal")

    source_module = db.Column(db.String(64), nullable=False)
    source_query = db.Column(db.Text, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id = db.Column(db.Integer, nullable=True)


class AnalyticsFact(db.Model):
    """Daily-grain facts with optional dimensional slices."""

    __tablename__ = "analytics_facts"
    __table_args__ = (
        UniqueConstraint(
            "org_id",
            "metric_key",
            "ts_date",
            "warehouse_id",
            "region",
            "user_id",
            "client_id",
            "item_id",
            name="uq_fact_grain",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    metric_key = db.Column(db.String(128), nullable=False, index=True)
    ts_date = db.Column(db.Date, nullable=False, index=True)

    warehouse_id = db.Column(db.Integer, nullable=True, index=True)
    region = db.Column(db.String(64), nullable=True, index=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    client_id = db.Column(db.Integer, nullable=True, index=True)
    item_id = db.Column(db.Integer, nullable=True, index=True)

    value = db.Column(db.Numeric(18, 4), nullable=False, default=Decimal("0"))

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class AnalyticsDashboard(db.Model):
    """Configurable dashboards that can be scoped to a role."""

    __tablename__ = "analytics_dashboards"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    name = db.Column(db.String(255), nullable=False)
    for_role = db.Column(db.String(64), nullable=True, index=True)

    is_default = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id = db.Column(db.Integer, nullable=True)

    widgets = db.relationship(
        "AnalyticsWidget",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        order_by="AnalyticsWidget.position.asc()",
    )


class AnalyticsWidget(db.Model):
    """One widget or chart shown on a dashboard."""

    __tablename__ = "analytics_widgets"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    dashboard_id = db.Column(
        db.Integer, db.ForeignKey("analytics_dashboards.id", ondelete="CASCADE"), nullable=False
    )

    title = db.Column(db.String(255), nullable=False)
    metric_key = db.Column(db.String(128), nullable=False, index=True)
    chart_type = db.Column(db.String(32), nullable=False, default="line")
    config_json = db.Column(db.JSON, nullable=False, default=dict)
    position = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    dashboard = db.relationship("AnalyticsDashboard", back_populates="widgets")


class DataLineage(db.Model):
    """Lineage and privacy notes for analytics metrics."""

    __tablename__ = "analytics_lineage"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    metric_key = db.Column(db.String(128), nullable=False, index=True)
    upstream_tables = db.Column(db.JSON, nullable=False, default=list)
    transformation = db.Column(db.Text, nullable=True)
    downstream_usage = db.Column(db.JSON, nullable=False, default=list)
    privacy_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
