"""Privacy compliance utilities and models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any, Iterable, Mapping

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db


@dataclass(slots=True)
class PrivacyFrameworkStatus:
    """Human-readable status for a certification or regulatory framework."""

    name: str
    state: str
    target: str
    owner: str
    next_audit: date | None = None


@dataclass(slots=True)
class PolicyLink:
    """Link to supporting privacy policies or procedures."""

    title: str
    description: str
    href: str


@dataclass(slots=True)
class UpcomingReview:
    """A privacy assessment that requires attention soon."""

    feature_name: str
    due_date: date
    days_remaining: int


@dataclass(slots=True)
class AssessmentSummary:
    """Aggregate metrics for privacy impact assessments."""

    total: int = 0
    high_risk_open: int = 0
    dsr_open: int = 0
    upcoming: list[UpcomingReview] = field(default_factory=list)


@dataclass(slots=True)
class PrivacyProgramSnapshot:
    """Snapshot rendered in the privacy dashboard."""

    frameworks: list[PrivacyFrameworkStatus]
    assessments: AssessmentSummary
    policies: list[PolicyLink]
    trust_service_criteria: list[str]
    review_warning_days: int
    officer_email: str


class PrivacyImpactAssessment(db.Model):  # type: ignore[name-defined]
    """Track Data Protection Impact Assessments and DSAR fulfilment."""

    __tablename__ = "privacy_impact_assessments"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_key = db.Column(db.String(128), nullable=False)
    feature_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="draft")
    risk_rating = db.Column(db.String(16), nullable=False, default="medium")
    assessment_date = db.Column(
        db.Date, default=lambda: datetime.now(UTC).date(), nullable=False
    )
    reviewer = db.Column(db.String(255), nullable=False)
    dpia_reference = db.Column(db.String(255))
    next_review_due = db.Column(
        db.Date,
        default=lambda: (datetime.now(UTC) + timedelta(days=365)).date(),
        nullable=False,
    )
    mitigation_summary = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "org_id", "feature_key", name="uq_privacy_assessment_feature"
        ),
        db.Index("ix_privacy_assessments_status", "status"),
        db.Index("ix_privacy_assessments_next_review", "next_review_due"),
    )

    def mark_reviewed(
        self, *, reviewer: str, next_due: date, status: str = "approved"
    ) -> None:
        """Update the assessment after review."""

        self.reviewer = reviewer
        self.status = status
        self.next_review_due = next_due
        self.updated_at = datetime.now(UTC)

    def is_high_risk(self) -> bool:
        """Return ``True`` when the assessment has unresolved high risk."""

        return (self.risk_rating or "").lower() == "high" and (
            self.status or ""
        ).lower() not in {"approved", "closed", "retired"}

    def is_dsr_open(self) -> bool:
        """Return ``True`` when a data subject request remains open."""

        status = (self.status or "").lower()
        return status.startswith("dsr-") and status not in {
            "dsr-closed",
            "dsr-complete",
        }


def _build_frameworks(officer_email: str) -> list[PrivacyFrameworkStatus]:
    """Return the curated list of framework statuses for the dashboard."""

    return [
        PrivacyFrameworkStatus(
            name="ISO/IEC 27001",
            state="In progress",
            target="Stage 2 certification evidence",
            owner=officer_email,
        ),
        PrivacyFrameworkStatus(
            name="ISO/IEC 27701",
            state="Planning",
            target="PIMS control mapping complete",
            owner=officer_email,
        ),
        PrivacyFrameworkStatus(
            name="SOC 2 Type II",
            state="Evidence collection",
            target="Trust Services Criteria coverage",
            owner="Security & Compliance",
        ),
        PrivacyFrameworkStatus(
            name="GDPR / CCPA",
            state="Operational",
            target="DSR SLA met and DPIAs current",
            owner="Privacy Squad",
        ),
    ]


def build_privacy_program_snapshot(config: Mapping[str, Any]) -> PrivacyProgramSnapshot:
    """Assemble the privacy program snapshot for the dashboard."""

    officer_email = str(config.get("PRIVACY_OFFICER_EMAIL", "privacy@berhan.example"))
    review_warning_days = int(config.get("PRIVACY_REVIEW_WARNING_DAYS", 45) or 45)
    dpiapath = str(config.get("PRIVACY_DPIA_TEMPLATE_PATH", "docs/DPIA_TEMPLATE.md"))
    docs_base = str(
        config.get(
            "PRIVACY_DOCS_BASE_URL",
            "https://github.com/getson7070/ERP-BERHAN/blob/main/",
        )
    )
    if docs_base and not docs_base.endswith("/"):
        docs_base = f"{docs_base}/"

    def _doc_href(path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return f"{docs_base}{path.lstrip('/')}"

    warning_cutoff = datetime.now(UTC).date() + timedelta(days=review_warning_days)
    try:
        assessments: Iterable[PrivacyImpactAssessment] = (
            PrivacyImpactAssessment.query.order_by(
                PrivacyImpactAssessment.next_review_due.asc()
            ).all()
        )
    except SQLAlchemyError as exc:  # pragma: no cover - defensive logging
        current_app.logger.warning("Failed to load privacy assessments: %s", exc)
        db.session.rollback()
        assessments = []

    assessments = list(assessments)
    today = datetime.now(UTC).date()
    upcoming: list[UpcomingReview] = []
    for assessment in assessments:
        if assessment.next_review_due:
            due_date = assessment.next_review_due
            if due_date <= warning_cutoff:
                upcoming.append(
                    UpcomingReview(
                        feature_name=assessment.feature_name,
                        due_date=due_date,
                        days_remaining=(due_date - today).days,
                    )
                )
    summary = AssessmentSummary(
        total=len(assessments),
        high_risk_open=sum(
            1 for assessment in assessments if assessment.is_high_risk()
        ),
        dsr_open=sum(1 for assessment in assessments if assessment.is_dsr_open()),
        upcoming=sorted(upcoming, key=lambda review: review.due_date),
    )

    policies = [
        PolicyLink(
            title="Privacy Program Charter",
            description="Roadmap for ISO/IEC 27001/27701 and SOC 2 alignment.",
            href=_doc_href("docs/PRIVACY_PROGRAM.md"),
        ),
        PolicyLink(
            title="GDPR & CCPA Data Handling",
            description="Operational procedures for consent, minimisation, and DSAR SLAs.",
            href=_doc_href("docs/DATA_HANDLING_PROCEDURES.md"),
        ),
        PolicyLink(
            title="DPIA Template",
            description="Assessment form for new features or processors that touch personal data.",
            href=_doc_href(dpiapath),
        ),
        PolicyLink(
            title="DSAR Runbook",
            description="Step-by-step instructions for fulfilling data subject requests.",
            href=_doc_href("docs/DSAR_RUNBOOK.md"),
        ),
    ]
    raw_criteria = config.get("SOC2_TRUST_SERVICE_CRITERIA", [])
    if isinstance(raw_criteria, (list, tuple, set)):
        criteria_source: Iterable[Any] = raw_criteria
    else:
        criteria_source = str(raw_criteria).split(",")
    trust_service_criteria = [
        str(criterion).strip()
        for criterion in criteria_source
        if str(criterion).strip()
    ]
    if not trust_service_criteria:
        trust_service_criteria = [
            "security",
            "availability",
            "processing-integrity",
            "confidentiality",
            "privacy",
        ]

    return PrivacyProgramSnapshot(
        frameworks=_build_frameworks(officer_email),
        assessments=summary,
        policies=policies,
        trust_service_criteria=trust_service_criteria,
        review_warning_days=review_warning_days,
        officer_email=officer_email,
    )


__all__ = [
    "AssessmentSummary",
    "PolicyLink",
    "PrivacyFrameworkStatus",
    "PrivacyImpactAssessment",
    "PrivacyProgramSnapshot",
    "UpcomingReview",
    "build_privacy_program_snapshot",
]


