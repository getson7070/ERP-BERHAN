"""tighten hr schema and enforce rls"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "h9i0j1k2l3m"
down_revision = "d4e5f6g7h8i"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    is_sqlite = dialect == "sqlite"

    # ───────────────────────────── hr_employees ─────────────────────────────
    if is_sqlite:
        # SQLite needs batch mode for adding constraints
        with op.batch_alter_table("hr_employees") as batch:
            batch.add_column(
                sa.Column(
                    "created_at",
                    sa.DateTime(),
                    nullable=False,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                )
            )
            batch.create_unique_constraint(
                "uq_hr_employees_org_name", ["org_id", "name"]
            )
    else:
        op.add_column(
            "hr_employees",
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        op.create_unique_constraint(
            "uq_hr_employees_org_name", "hr_employees", ["org_id", "name"]
        )

    # ───────────────────────────── hr_recruitment ───────────────────────────
    if is_sqlite:
        with op.batch_alter_table("hr_recruitment") as batch:
            batch.create_foreign_key(
                "fk_hr_recruitment_org",
                "organizations",
                ["org_id"],
                ["id"],
                ondelete="CASCADE",
            )
            batch.create_unique_constraint(
                "uq_hr_recruitment_candidate",
                ["org_id", "candidate_name", "position"],
            )
            batch.create_check_constraint(
                "chk_hr_recruitment_status",
                "status in ('applied','shortlisted','approved')",
            )
        # Partial/filtered index: emulate with sqlite_where
        op.create_index(
            "ix_hr_recruitment_pending",
            "hr_recruitment",
            ["org_id", "status"],
            sqlite_where=sa.text("status != 'approved'"),
        )
    else:
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
        # RLS & partial index are Postgres-only
        op.execute("ALTER TABLE hr_recruitment ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY hr_recruitment_org_isolation "
            "ON hr_recruitment USING (org_id = current_setting('erp.org_id')::int)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_hr_recruitment_pending "
            "ON hr_recruitment (org_id, status) WHERE status <> 'approved'"
        )

    # ──────────────────────── hr_performance_reviews ────────────────────────
    if is_sqlite:
        with op.batch_alter_table("hr_performance_reviews") as batch:
            batch.create_foreign_key(
                "fk_hr_performance_reviews_org",
                "organizations",
                ["org_id"],
                ["id"],
                ondelete="CASCADE",
            )
            batch.create_check_constraint(
                "chk_performance_score", "score >= 1 AND score <= 5"
            )
            batch.create_unique_constraint(
                "uq_hr_performance_once",
                ["org_id", "employee_name", "review_date"],
            )
        op.create_index(
            "ix_hr_performance_reviews_review_date",
            "hr_performance_reviews",
            ["review_date"],
        )
    else:
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
        op.execute("ALTER TABLE hr_performance_reviews ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY hr_performance_reviews_org_isolation "
            "ON hr_performance_reviews USING (org_id = current_setting('erp.org_id')::int)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    is_sqlite = dialect == "sqlite"

    # hr_performance_reviews
    if not is_sqlite:
        op.execute(
            "DROP POLICY IF EXISTS hr_performance_reviews_org_isolation "
            "ON hr_performance_reviews"
        )
    op.drop_index(
        "ix_hr_performance_reviews_review_date",
        table_name="hr_performance_reviews",
    )

    if is_sqlite:
        with op.batch_alter_table("hr_performance_reviews") as batch:
            batch.drop_constraint(
                "uq_hr_performance_once", type_="unique"
            )
            batch.drop_constraint(
                "chk_performance_score", type_="check"
            )
            batch.drop_constraint(
                "fk_hr_performance_reviews_org", type_="foreignkey"
            )
    else:
        op.drop_constraint(
            "uq_hr_performance_once", "hr_performance_reviews", type_="unique"
        )
        op.drop_constraint(
            "chk_performance_score", "hr_performance_reviews", type_="check"
        )
        op.drop_constraint(
            "fk_hr_performance_reviews_org",
            "hr_performance_reviews",
            type_="foreignkey",
        )

    # hr_recruitment
    if not is_sqlite:
        op.execute(
            "DROP POLICY IF EXISTS hr_recruitment_org_isolation ON hr_recruitment"
        )
        op.execute("DROP INDEX IF EXISTS ix_hr_recruitment_pending")
    else:
        op.drop_index("ix_hr_recruitment_pending", table_name="hr_recruitment")

    if is_sqlite:
        with op.batch_alter_table("hr_recruitment") as batch:
            batch.drop_constraint(
                "chk_hr_recruitment_status", type_="check"
            )
            batch.drop_constraint(
                "uq_hr_recruitment_candidate", type_="unique"
            )
            batch.drop_constraint(
                "fk_hr_recruitment_org", type_="foreignkey"
            )
    else:
        op.drop_constraint(
            "chk_hr_recruitment_status", "hr_recruitment", type_="check"
        )
        op.drop_constraint(
            "uq_hr_recruitment_candidate", "hr_recruitment", type_="unique"
        )
        op.drop_constraint(
            "fk_hr_recruitment_org", "hr_recruitment", type_="foreignkey"
        )

    # hr_employees
    if is_sqlite:
        with op.batch_alter_table("hr_employees") as batch:
            batch.drop_constraint(
                "uq_hr_employees_org_name", type_="unique"
            )
            batch.drop_column("created_at")
    else:
        op.drop_constraint(
            "uq_hr_employees_org_name", "hr_employees", type_="unique"
        )
        op.drop_column("hr_employees", "created_at")
