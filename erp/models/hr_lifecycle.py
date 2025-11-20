"""HR lifecycle models covering onboarding, offboarding, reviews, and leave."""

from __future__ import annotations

from datetime import UTC, date, datetime

from erp.extensions import db


class HROnboarding(db.Model):
    __tablename__ = "hr_onboarding"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_date = db.Column(db.Date, nullable=False)
    contract_type = db.Column(db.String(32), nullable=False)
    checklist_json = db.Column(db.JSON, nullable=False, default=dict)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_by_id = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    employee = db.relationship("Employee", backref=db.backref("onboarding_records", lazy=True))


class HROffboarding(db.Model):
    __tablename__ = "hr_offboarding"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason = db.Column(db.String(255), nullable=False)
    last_working_day = db.Column(db.Date, nullable=False)
    checklist_json = db.Column(db.JSON, nullable=False, default=dict)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_by_id = db.Column(db.Integer, nullable=True)

    employee = db.relationship("Employee", backref=db.backref("offboarding_records", lazy=True))


class PerformanceReview(db.Model):
    __tablename__ = "performance_reviews"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    employee_name = db.Column(db.String(255), nullable=True)
    review_date = db.Column(db.Date, nullable=False, default=date.today)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.String(32), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    goals = db.Column(db.Text, nullable=True)
    competencies = db.Column(db.Text, nullable=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    employee = db.relationship("Employee", backref=db.backref("performance_reviews", lazy=True))

    @property
    def is_active_period(self) -> bool:
        today = date.today()
        return self.period_start <= today <= self.period_end

    def finalize(self) -> None:
        self.status = "final"
        self.completed_at = datetime.now(UTC)

    @classmethod
    def tenant_query(cls, org_id: int | None = None):
        query = cls.query
        if org_id is not None:
            query = query.filter_by(organization_id=org_id)
        return query


class LeaveRequest(db.Model):
    __tablename__ = "leave_requests"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, nullable=False, index=True)
    employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    leave_type = db.Column(db.String(32), nullable=False)
    reason = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(16), nullable=False, default="pending")
    approver_id = db.Column(db.Integer, nullable=True)
    decided_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    employee = db.relationship("Employee", backref=db.backref("leave_requests", lazy=True))

    @classmethod
    def tenant_query(cls, org_id: int | None = None):
        query = cls.query
        if org_id is not None:
            query = query.filter_by(organization_id=org_id)
        return query
