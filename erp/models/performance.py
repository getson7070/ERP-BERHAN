"""Performance KPIs, scorecards, reviews, and ML suggestion scaffolding."""
from __future__ import annotations

from sqlalchemy import UniqueConstraint, func
from erp.extensions import db


class KPIRegistry(db.Model):
    """Defines KPI metadata and scoring rules; facts live in :class:`AnalyticsFact`."""

    __tablename__ = "kpi_registry"
    __table_args__ = (UniqueConstraint("org_id", "kpi_key", name="uq_kpi_key"),)

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    kpi_key = db.Column(db.String(128), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    target_value = db.Column(db.Numeric(18, 4), nullable=True)
    weight = db.Column(db.Numeric(6, 4), nullable=False, default=1.0)
    direction = db.Column(db.String(16), nullable=False, default="higher_better")
    min_score = db.Column(db.Numeric(6, 3), nullable=False, default=0)
    max_score = db.Column(db.Numeric(6, 3), nullable=False, default=100)

    privacy_class = db.Column(db.String(32), nullable=False, default="internal")
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id = db.Column(db.Integer, nullable=True)


class ScorecardTemplate(db.Model):
    """Groups KPIs for a specific subject type (employee, client, inventory, order, warehouse)."""

    __tablename__ = "scorecard_templates"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    name = db.Column(db.String(255), nullable=False)
    subject_type = db.Column(db.String(32), nullable=False, index=True)

    is_default = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    created_by_id = db.Column(db.Integer, nullable=True)

    items = db.relationship(
        "ScorecardItem",
        back_populates="template",
        cascade="all, delete-orphan",
    )


class ScorecardItem(db.Model):
    """KPI membership inside a scorecard with optional overrides."""

    __tablename__ = "scorecard_items"
    __table_args__ = (UniqueConstraint("org_id", "template_id", "kpi_key", name="uq_scorecard_kpi"),)

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    template_id = db.Column(
        db.Integer,
        db.ForeignKey("scorecard_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    kpi_key = db.Column(db.String(128), nullable=False, index=True)
    weight_override = db.Column(db.Numeric(6, 4), nullable=True)
    target_override = db.Column(db.Numeric(18, 4), nullable=True)

    template = db.relationship("ScorecardTemplate", back_populates="items")


class ReviewCycle(db.Model):
    """Defines a review period (monthly, quarterly, annual)."""

    __tablename__ = "review_cycles"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)

    status = db.Column(db.String(32), nullable=False, default="open", index=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class PerformanceEvaluation(db.Model):
    """Computed evaluation with KPI breakdown for a subject within a cycle."""

    __tablename__ = "performance_evaluations"
    __table_args__ = (
        UniqueConstraint(
            "org_id", "cycle_id", "subject_type", "subject_id", name="uq_eval_subject_cycle"
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    cycle_id = db.Column(db.Integer, db.ForeignKey("review_cycles.id"), nullable=False, index=True)

    subject_type = db.Column(db.String(32), nullable=False, index=True)
    subject_id = db.Column(db.Integer, nullable=False, index=True)

    scorecard_template_id = db.Column(db.Integer, nullable=True, index=True)
    total_score = db.Column(db.Numeric(6, 3), nullable=False, default=0)
    breakdown_json = db.Column(db.JSON, nullable=False, default=dict)

    status = db.Column(db.String(32), nullable=False, default="computed", index=True)

    computed_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    reviewed_by_id = db.Column(db.Integer, nullable=True)
    approved_by_id = db.Column(db.Integer, nullable=True)


class Feedback360(db.Model):
    """Qualitative 360-degree feedback tied to an evaluation."""

    __tablename__ = "feedback_360"

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    evaluation_id = db.Column(
        db.BigInteger,
        db.ForeignKey("performance_evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    giver_type = db.Column(db.String(32), nullable=False, default="user")
    giver_id = db.Column(db.Integer, nullable=False, index=True)

    rating = db.Column(db.Numeric(4, 2), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    dimension = db.Column(db.String(64), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class MLSuggestion(db.Model):
    """Placeholder for ML-driven insights such as training needs or churn risk."""

    __tablename__ = "ml_suggestions"

    id = db.Column(db.BigInteger, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)

    cycle_id = db.Column(db.Integer, nullable=False, index=True)
    subject_type = db.Column(db.String(32), nullable=False, index=True)
    subject_id = db.Column(db.Integer, nullable=False, index=True)

    suggestion_type = db.Column(db.String(64), nullable=False, index=True)
    confidence = db.Column(db.Numeric(4, 3), nullable=False, default=0.5)
    reason_json = db.Column(db.JSON, nullable=False, default=dict)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
