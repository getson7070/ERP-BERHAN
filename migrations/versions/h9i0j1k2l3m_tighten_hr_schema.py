"""tighten hr schema and enforce rls (existence-aware & sqlite-safe)"""

from alembic import op
import sqlalchemy as sa

revision = "h9i0j1k2l3m"
down_revision = "d4e5f6g7h8i"
branch_labels = None
depends_on = None


def _table_exists(insp, name: str) -> bool:
    try:
        return insp.has_table(name)
    except Exception:
        return False


def _columns(insp, table):
    try:
        return {c["name"] for c in insp.get_columns(table)}
    except Exception:
        return set()


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dialect = bind.dialect.name

    # -------------------------
    # hr_employees adjustments
    # -------------------------
    if _table_exists(insp, "hr_employees"):
        cols = _columns(insp, "hr_employees")

        # Add created_at if missing
        if "created_at" not in cols:
            if dialect == "sqlite":
                with op.batch_alter_table("hr_employees") as batch:
                    batch.add_column(
                        sa.Column(
                            "created_at",
                            sa.DateTime(),
                            nullable=False,
                            server_default=sa.text("CURRENT_TIMESTAMP"),
                        )
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

        # Unique (org_id, name) via index (works on SQLite & Postgres)
        op.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_hr_employees_org_name ON hr_employees (org_id, name)"
        )

    # -------------------------
    # hr_recruitment constraints / indexes / RLS
    # -------------------------
    if _table_exists(insp, "hr_recruitment"):
        r_cols = _columns(insp, "hr_recruitment")

        # FK to organizations (Postgres only, add if missing)
        if (
            dialect != "sqlite"
            and _table_exists(insp, "organizations")
            and "org_id" in r_cols
        ):
            op.execute(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                      SELECT 1 FROM pg_constraint
                      WHERE conname = 'fk_hr_recruitment_org'
                  ) THEN
                    ALTER TABLE hr_recruitment
                    ADD CONSTRAINT fk_hr_recruitment_org
                    FOREIGN KEY (org_id) REFERENCES organizations(id)
                    ON DELETE CASCADE;
                  END IF;
                END $$;
                """
            )

        # Unique (org_id, candidate_name, position) via index
        if {"org_id", "candidate_name", "position"}.issubset(r_cols):
            op.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_hr_recruitment_candidate
                ON hr_recruitment (org_id, candidate_name, position)
                """
            )

        # Pending index
        if {"org_id", "status"}.issubset(r_cols):
            if dialect == "sqlite":
                op.execute(
                    """
                    CREATE INDEX IF NOT EXISTS ix_hr_recruitment_pending
                    ON hr_recruitment (org_id, status)
                    """
                )
            else:
                op.execute(
                    """
                    CREATE INDEX IF NOT EXISTS ix_hr_recruitment_pending
                    ON hr_recruitment (org_id, status)
                    WHERE status <> 'approved'
                    """
                )

        # RLS (Postgres only)
        if dialect != "sqlite":
            op.execute("ALTER TABLE IF EXISTS hr_recruitment ENABLE ROW LEVEL SECURITY")
            op.execute(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                      SELECT 1 FROM pg_policies
                      WHERE schemaname = 'public'
                        AND tablename  = 'hr_recruitment'
                        AND policyname = 'hr_recruitment_org_isolation'
                  ) THEN
                    CREATE POLICY hr_recruitment_org_isolation
                    ON hr_recruitment
                    USING (org_id = current_setting('erp.org_id', true)::int);
                  END IF;
                END $$;
                """
            )

    # -------------------------
    # hr_performance_reviews constraints / indexes / RLS
    # -------------------------
    if _table_exists(insp, "hr_performance_reviews"):
        p_cols = _columns(insp, "hr_performance_reviews")

        # Check constraint (Postgres)
        if dialect != "sqlite" and {"score"}.issubset(p_cols):
            op.execute(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                      SELECT 1 FROM pg_constraint
                      WHERE conname = 'chk_performance_score'
                  ) THEN
                    ALTER TABLE hr_performance_reviews
                    ADD CONSTRAINT chk_performance_score
                    CHECK (score >= 1 AND score <= 5);
                  END IF;
                END $$;
                """
            )

        # Unique once per (org_id, employee_name, review_date)
        if {"org_id", "employee_name", "review_date"}.issubset(p_cols):
            op.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_hr_performance_once
                ON hr_performance_reviews (org_id, employee_name, review_date)
                """
            )

        # Index on review_date
        if "review_date" in p_cols:
            op.execute(
                "CREATE INDEX IF NOT EXISTS ix_hr_performance_reviews_review_date ON hr_performance_reviews (review_date)"
            )

        # RLS (Postgres)
        if dialect != "sqlite":
            op.execute("ALTER TABLE IF EXISTS hr_performance_reviews ENABLE ROW LEVEL SECURITY")
            op.execute(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                      SELECT 1 FROM pg_policies
                      WHERE schemaname = 'public'
                        AND tablename  = 'hr_performance_reviews'
                        AND policyname = 'hr_performance_reviews_org_isolation'
                  ) THEN
                    CREATE POLICY hr_performance_reviews_org_isolation
                    ON hr_performance_reviews
                    USING (org_id = current_setting('erp.org_id', true)::int);
                  END IF;
                END $$;
                """
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dialect = bind.dialect.name

    if dialect != "sqlite":
        op.execute(
            "DROP POLICY IF EXISTS hr_performance_reviews_org_isolation ON hr_performance_reviews"
        )
        op.execute(
            "DROP POLICY IF EXISTS hr_recruitment_org_isolation ON hr_recruitment"
        )

    if _table_exists(insp, "hr_performance_reviews"):
        op.execute("DROP INDEX IF EXISTS ix_hr_performance_reviews_review_date")
        op.execute("DROP INDEX IF EXISTS uq_hr_performance_once")

    if _table_exists(insp, "hr_recruitment"):
        op.execute("DROP INDEX IF EXISTS ix_hr_recruitment_pending")
        op.execute("DROP INDEX IF EXISTS uq_hr_recruitment_candidate")

    if _table_exists(insp, "hr_employees"):
        op.execute("DROP INDEX IF EXISTS uq_hr_employees_org_name")
        cols = _columns(insp, "hr_employees")
        if "created_at" in cols:
            if dialect == "sqlite":
                with op.batch_alter_table("hr_employees") as batch:
                    batch.drop_column("created_at")
            else:
                op.drop_column("hr_employees", "created_at")
