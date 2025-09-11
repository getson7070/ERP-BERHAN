"""tighten hr schema and enforce rls"""

from alembic import op
import sqlalchemy as sa

revision = "h9i0j1k2l3m"
down_revision = "d4e5f6g7h8i"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "hr_employees",
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_unique_constraint(
        "uq_hr_employees_org_name", "hr_employees", ["org_id", "name"]
    )

    # recruitment constraints and RLS
    op.create_foreign_key(
        "fk_hr_recruitment_org",
        "hr_recruitment",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_hr_recruitment_candidate",
        "hr_recruitment",
        ["org_id", "candidate_name", "position"],
    )
    op.create_check_constraint(
        "chk_hr_recruitment_status",
        "hr_recruitment",
        "status in ('applied','shortlisted','approved')",
    )
    if op.get_bind().dialect.name != "sqlite":
        op.execute("ALTER TABLE hr_recruitment ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY hr_recruitment_org_isolation ON hr_recruitment USING (org_id = current_setting('erp.org_id')::int)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_hr_recruitment_pending ON hr_recruitment (org_id, status) WHERE status <> 'approved'"
        )
    else:
        op.create_index(
            "ix_hr_recruitment_pending",
            "hr_recruitment",
            ["org_id", "status"],
            sqlite_where=sa.text("status != 'approved'"),
        )

    # performance review constraints and RLS
    op.create_foreign_key(
        "fk_hr_performance_reviews_org",
        "hr_performance_reviews",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "chk_performance_score",
        "hr_performance_reviews",
        "score >= 1 AND score <= 5",
    )
    op.create_unique_constraint(
        "uq_hr_performance_once",
        "hr_performance_reviews",
        ["org_id", "employee_name", "review_date"],
    )
    op.create_index(
        "ix_hr_performance_reviews_review_date",
        "hr_performance_reviews",
        ["review_date"],
    )
    if op.get_bind().dialect.name != "sqlite":
        op.execute("ALTER TABLE hr_performance_reviews ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY hr_performance_reviews_org_isolation ON hr_performance_reviews USING (org_id = current_setting('erp.org_id')::int)"
        )


def downgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        op.execute(
            "DROP POLICY IF EXISTS hr_performance_reviews_org_isolation ON hr_performance_reviews"
        )
        op.execute(
            "DROP POLICY IF EXISTS hr_recruitment_org_isolation ON hr_recruitment"
        )
    op.drop_index(
        "ix_hr_performance_reviews_review_date",
        table_name="hr_performance_reviews",
    )
    op.drop_constraint(
        "uq_hr_performance_once", "hr_performance_reviews", type_="unique"
    )
    op.drop_constraint("chk_performance_score", "hr_performance_reviews", type_="check")
    op.drop_constraint(
        "fk_hr_performance_reviews_org", "hr_performance_reviews", type_="foreignkey"
    )
    if op.get_bind().dialect.name != "sqlite":
        op.execute("DROP INDEX IF EXISTS ix_hr_recruitment_pending")
    else:
        op.drop_index("ix_hr_recruitment_pending", table_name="hr_recruitment")
    op.drop_constraint("chk_hr_recruitment_status", "hr_recruitment", type_="check")
    op.drop_constraint("uq_hr_recruitment_candidate", "hr_recruitment", type_="unique")
    op.drop_constraint("fk_hr_recruitment_org", "hr_recruitment", type_="foreignkey")
    op.drop_constraint("uq_hr_employees_org_name", "hr_employees", type_="unique")
    op.drop_column("hr_employees", "created_at")
