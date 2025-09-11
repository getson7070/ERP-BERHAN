"""add hr workflow tables"""

from alembic import op
import sqlalchemy as sa

revision = "g1h2i3j4k5l"
down_revision = "f0e1d2c3b4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hr_recruitment",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, nullable=False),
        sa.Column("candidate_name", sa.String(length=120), nullable=False),
        sa.Column("position", sa.String(length=120), nullable=False),
        sa.Column("applied_on", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_hr_recruitment_org_id", "hr_recruitment", ["org_id"])

    op.create_table(
        "hr_performance_reviews",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, nullable=False),
        sa.Column("employee_name", sa.String(length=120), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("review_date", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_hr_performance_reviews_org_id",
        "hr_performance_reviews",
        ["org_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_hr_performance_reviews_org_id", table_name="hr_performance_reviews"
    )
    op.drop_table("hr_performance_reviews")
    op.drop_index("ix_hr_recruitment_org_id", table_name="hr_recruitment")
    op.drop_table("hr_recruitment")
