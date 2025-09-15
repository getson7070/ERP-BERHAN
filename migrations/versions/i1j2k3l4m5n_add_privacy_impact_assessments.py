"""add privacy impact assessments table"""

import sqlalchemy as sa
from alembic import op

revision = "i1j2k3l4m5n"
down_revision = "h9i0j1k2l3m"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "privacy_impact_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("feature_key", sa.String(length=128), nullable=False),
        sa.Column("feature_name", sa.String(length=255), nullable=False),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="draft"
        ),
        sa.Column(
            "risk_rating", sa.String(length=16), nullable=False, server_default="medium"
        ),
        sa.Column(
            "assessment_date",
            sa.Date(),
            nullable=False,
            server_default=sa.func.current_date(),
        ),
        sa.Column("reviewer", sa.String(length=255), nullable=False),
        sa.Column("dpia_reference", sa.String(length=255)),
        sa.Column(
            "next_review_due",
            sa.Date(),
            nullable=False,
            server_default=sa.func.current_date(),
        ),
        sa.Column("mitigation_summary", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "org_id", "feature_key", name="uq_privacy_assessment_feature"
        ),
    )
    op.create_index(
        "ix_privacy_assessments_status",
        "privacy_impact_assessments",
        ["status"],
    )
    op.create_index(
        "ix_privacy_assessments_next_review",
        "privacy_impact_assessments",
        ["next_review_due"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_privacy_assessments_next_review", table_name="privacy_impact_assessments"
    )
    op.drop_index(
        "ix_privacy_assessments_status", table_name="privacy_impact_assessments"
    )
    op.drop_table("privacy_impact_assessments")
