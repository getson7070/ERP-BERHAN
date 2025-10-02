"""tighten hr schema and enforce rls (idempotent & sqlite-safe)"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = "h9i0j1k2l3m"
down_revision = "d4e5f6g7h8i"
branch_labels = None
depends_on = None


# ───────────────────────── helpers ─────────────────────────
def _has_column(conn, table: str, column: str) -> bool:
    insp = sa.inspect(conn)
    try:
        return any(col["name"] == column for col in insp.get_columns(table))
    except Exception:
        return False


def _pg_constraint_exists(conn, name: str) -> bool:
    if conn.dialect.name != "postgresql":
        return False
    row = conn.execute(sa.text("SELECT 1 FROM pg_constraint WHERE conname=:n"), {"n": name}).fetchone()
    return bool(row)


# ───────────────────────── upgrade ─────────────────────────
def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # --- hr_employees: created_at (guarded) ---
    if not _has_column(conn, "hr_employees", "created_at"):
        col = sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now())
        if dialect == "sqlite":
            with op.batch_alter_table("hr_employees") as batch:
                batch.add_column(col)
        else:
            op.add_column("hr_employees", col)

    # --- hr_employees: unique (org_id, name) ---
    if dialect == "sqlite":
        with op.batch_alter_table("hr_employees") as batch:
            batch.create_unique_constraint("uq_hr_employees_org_name", ["org_id", "name"])
    elif dialect == "postgresql":
        if not _pg_constraint_exists(conn, "uq_hr_employees_org_name"):
            op.create_unique_constraint("uq_hr_employees_org_name", "hr_employees", ["org_id", "name"])
    else:
        op.create_unique_constraint("uq_hr_employees_org_name", "hr_employees", ["org_id", "name"])

    # --- hr_recruitment: FKs/uniques/checks/index/RLS ---
    if dialect == "sqlite":
        with op.batch_alter_table("hr_recruitment") as batch:
            batch.create_foreign_key(
                "fk_hr_recruitment_org", "organizations", ["org_id"], ["id"], ondelete="CASCADE"
            )
            batch.create_unique_constraint(
                "uq_hr_recruitment_candidate", ["org_id", "candidate_name", "position"]
            )
            batch.create_check_constraint(
                "chk_hr_recruitment_status",
                "status in ('applied','shortlisted','approved')",
            )
        # partial index emulation for SQLite
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
        op.execute(
            sa.text(
                "CREATE INDEX IF NOT EXISTS ix_hr_recruitment_pending "
                "ON hr_recruitment (org_id, status) WHERE status <> 'approved'"
            )
        )
        if dialect == "postgresql":
            op.execute(sa.text("ALTER TABLE hr_recruitment ENABLE ROW LEVEL SECURITY"))
            op.execute(
                sa.text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE polname='hr_recruitment_org_isolation') THEN "
                    "CREATE POLICY hr_recruitment_org_isolation ON hr_recruitment "
                    "USING (org_id = current_setting('erp.org_id')::int); "
                    "END IF; END $$;"
                )
            )

    # --- hr_performance_reviews: FKs/uniques/checks/index/RLS ---
    if dialect == "sqlite":
        with op.batch_alter_table("hr_performance_reviews") as batch:
            batch.create_foreign_key(
                "fk_hr_performance_reviews_org", "organizations", ["org_id"], ["id"], ondelete="CASCADE"
            )
            batch.create_check_constraint("chk_performance_score", "score >= 1 AND score <= 5")
            batch.create_unique_constraint(
                "uq_hr_performance_once", ["org_id", "employee_name", "review_date"]
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
        if dialect == "postgresql":
            op.execute(sa.text("ALTER TABLE hr_performance_reviews ENABLE ROW LEVEL SECURITY"))
            op.execute(
                sa.text(
                    "DO $$ BEGIN "
                    "IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE polname='hr_performance_reviews_org_isolation') THEN "
                    "CREATE POLICY hr_performance_reviews_org_isolation ON hr_performance_reviews "
                    "USING (org_id = current_setting('erp.org_id')::int); "
                    "END IF; END $$;"
                )
            )


# ───────────────────────── downgrade ─────────────────────────
def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # indexes
    op.drop_index("ix_hr_performance_reviews_review_date", table_name="hr_performance_reviews")
    if dialect == "sqlite":
        op.drop_index("ix_hr_recruitment_pending", table_name="hr_recruitment")
    else:
        op.execute(sa.text("DROP INDEX IF EXISTS ix_hr_recruitment_pending"))

    if dialect == "sqlite":
        with op.batch_alter_table("hr_performance_reviews") as batch:
            batch.drop_constraint("uq_hr_performance_once", type_="unique")
            batch.drop_constraint("chk_performance_score", type_="check")
            batch.drop_constraint("fk_hr_performance_reviews_org", type_="foreignkey")
        with op.batch_alter_table("hr_employees") as batch:
            batch.drop_constraint("uq_hr_employees_org_name", type_="unique")
            if _has_column(conn, "hr_employees", "created_at"):
                batch.drop_column("created_at")
        with op.batch_alter_table("hr_recruitment") as batch:
            batch.drop_constraint("chk_hr_recruitment_status", type_="check")
            batch.drop_constraint("uq_hr_recruitment_candidate", type_="unique")
            batch.drop_constraint("fk_hr_recruitment_org", type_="foreignkey")
    else:
        op.drop_constraint("uq_hr_performance_once", "hr_performance_reviews", type_="unique")
        op.drop_constraint("chk_performance_score", "hr_performance_reviews", type_="check")
        op.drop_constraint("fk_hr_performance_reviews_org", "hr_performance_reviews", type_="foreignkey")
        op.drop_constraint("uq_hr_employees_org_name", "hr_employees", type_="unique")
        if _has_column(conn, "hr_employees", "created_at"):
            op.drop_column("hr_employees", "created_at")
        op.drop_constraint("chk_hr_recruitment_status", "hr_recruitment", type_="check")
        op.drop_constraint("uq_hr_recruitment_candidate", "hr_recruitment", type_="unique")
        op.drop_constraint("fk_hr_recruitment_org", "hr_recruitment", type_="foreignkey")
        if dialect == "postgresql":
            op.execute(sa.text("DROP POLICY IF EXISTS hr_performance_reviews_org_isolation ON hr_performance_reviews"))
            op.execute(sa.text("DROP POLICY IF EXISTS hr_recruitment_org_isolation ON hr_recruitment"))
