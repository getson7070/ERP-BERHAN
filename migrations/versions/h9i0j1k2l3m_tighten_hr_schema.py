"""tighten hr schema and enforce rls (idempotent & SQLite-safe)"""

from alembic import op
import sqlalchemy as sa

revision = "h9i0j1k2l3m"
down_revision = "d4e5f6g7h8i"
branch_labels = None
depends_on = None


def _has_column(insp, table, colname):
    return colname in {c["name"] for c in insp.get_columns(table)}


def _uq_names(insp, table):
    # Some dialects may return None for unnamed UQs
    return { (uc.get("name") or "") for uc in insp.get_unique_constraints(table) }


def _ck_names(insp, table):
    try:
        return { (ck.get("name") or "") for ck in insp.get_check_constraints(table) }
    except Exception:
        return set()


def _fk_names(insp, table):
    return { (fk.get("name") or "") for fk in insp.get_foreign_keys(table) }


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dialect = bind.dialect.name

    # -------------------- hr_employees --------------------
    # add created_at if missing + create UQ in batch (SQLite needs batch mode)
    with op.batch_alter_table("hr_employees", recreate="auto") as batch:
        if not _has_column(insp, "hr_employees", "created_at"):
            batch.add_column(
                sa.Column(
                    "created_at",
                    sa.DateTime(),
                    nullable=False,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                )
            )

        if "uq_hr_employees_org_name" not in _uq_names(insp, "hr_employees"):
            batch.create_unique_constraint(
                "uq_hr_employees_org_name", ["org_id", "name"]
            )

    # -------------------- hr_recruitment --------------------
    existing_fks = _fk_names(insp, "hr_recruitment")
    existing_uqs = _uq_names(insp, "hr_recruitment")
    existing_cks = _ck_names(insp, "hr_recruitment")

    with op.batch_alter_table("hr_recruitment", recreate="auto") as batch:
        if "fk_hr_recruitment_org" not in existing_fks:
            batch.create_foreign_key(
                "fk_hr_recruitment_org",
                "organizations",
                ["org_id"],
                ["id"],
                ondelete="CASCADE",
            )

        if "uq_hr_recruitment_candidate" not in existing_uqs:
            batch.create_unique_constraint(
                "uq_hr_recruitment_candidate",
                ["org_id", "candidate_name", "position"],
            )

        if "chk_hr_recruitment_status" not in existing_cks:
            batch.create_check_constraint(
                "chk_hr_recruitment_status",
                "status in ('applied','shortlisted','approved')",
            )

    # Partial index differs by dialect
    if dialect == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_hr_recruitment_pending "
            "ON hr_recruitment (org_id, status) WHERE status <> 'approved'"
        )
        # Enable RLS & policy (no-ops on SQLite)
        op.execute("ALTER TABLE hr_recruitment ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY IF NOT EXISTS hr_recruitment_org_isolation "
            "ON hr_recruitment USING (org_id = current_setting('erp.org_id')::int)"
        )
    else:
        # SQLite: emulate partial index with sqlite_where
        # If it already exists, create_index will raise; so guard by name
        existing_idxs = {ix["name"] for ix in insp.get_indexes("hr_recruitment")}
        if "ix_hr_recruitment_pending" not in existing_idxs:
            op.create_index(
                "ix_hr_recruitment_pending",
                "hr_recruitment",
                ["org_id", "status"],
                sqlite_where=sa.text("status != 'approved'"),
            )

    # -------------------- hr_performance_reviews --------------------
    existing_fks = _fk_names(insp, "hr_performance_reviews")
    existing_uqs = _uq_names(insp, "hr_performance_reviews")
    existing_cks = _ck_names(insp, "hr_performance_reviews")
    existing_idxs = {ix["name"] for ix in insp.get_indexes("hr_performance_reviews")}

    with op.batch_alter_table("hr_performance_reviews", recreate="auto") as batch:
        if "fk_hr_performance_reviews_org" not in existing_fks:
            batch.create_foreign_key(
                "fk_hr_performance_reviews_org",
                "organizations",
                ["org_id"],
                ["id"],
                ondelete="CASCADE",
            )

        if "chk_performance_score" not in existing_cks:
            batch.create_check_constraint(
                "chk_performance_score", "score >= 1 AND score <= 5"
            )

        if "uq_hr_performance_once" not in existing_uqs:
            batch.create_unique_constraint(
                "uq_hr_performance_once",
                ["org_id", "employee_name", "review_date"],
            )

        if "ix_hr_performance_reviews_review_date" not in existing_idxs:
            batch.create_index(
                "ix_hr_performance_reviews_review_date", ["review_date"]
            )

    if dialect == "postgresql":
        op.execute("ALTER TABLE hr_performance_reviews ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY IF NOT EXISTS hr_performance_reviews_org_isolation "
            "ON hr_performance_reviews USING (org_id = current_setting('erp.org_id')::int)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    dialect = bind.dialect.name

    # hr_performance_reviews
    with op.batch_alter_table("hr_performance_reviews", recreate="auto") as batch:
        if "ix_hr_performance_reviews_review_date" in {
            ix["name"] for ix in insp.get_indexes("hr_performance_reviews")
        }:
            batch.drop_index("ix_hr_performance_reviews_review_date")
        if "uq_hr_performance_once" in _uq_names(insp, "hr_performance_reviews"):
            batch.drop_constraint("uq_hr_performance_once", type_="unique")
        if "chk_performance_score" in _ck_names(insp, "hr_performance_reviews"):
            batch.drop_constraint("chk_performance_score", type_="check")
        if "fk_hr_performance_reviews_org" in _fk_names(insp, "hr_performance_reviews"):
            batch.drop_constraint("fk_hr_performance_reviews_org", type_="foreignkey")

    if dialect == "postgresql":
        op.execute(
            "DROP POLICY IF EXISTS hr_performance_reviews_org_isolation ON hr_performance_reviews"
        )

    # hr_recruitment
    if dialect == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_hr_recruitment_pending")
    else:
        if "ix_hr_recruitment_pending" in {
            ix["name"] for ix in insp.get_indexes("hr_recruitment")
        }:
            op.drop_index("ix_hr_recruitment_pending", table_name="hr_recruitment")

    with op.batch_alter_table("hr_recruitment", recreate="auto") as batch:
        if "chk_hr_recruitment_status" in _ck_names(insp, "hr_recruitment"):
            batch.drop_constraint("chk_hr_recruitment_status", type_="check")
        if "uq_hr_recruitment_candidate" in _uq_names(insp, "hr_recruitment"):
            batch.drop_constraint("uq_hr_recruitment_candidate", type_="unique")
        if "fk_hr_recruitment_org" in _fk_names(insp, "hr_recruitment"):
            batch.drop_constraint("fk_hr_recruitment_org", type_="foreignkey")

    if dialect == "postgresql":
        op.execute(
            "DROP POLICY IF EXISTS hr_recruitment_org_isolation ON hr_recruitment"
        )

    # hr_employees
    with op.batch_alter_table("hr_employees", recreate="auto") as batch:
        if "uq_hr_employees_org_name" in _uq_names(insp, "hr_employees"):
            batch.drop_constraint("uq_hr_employees_org_name", type_="unique")
        if _has_column(insp, "hr_employees", "created_at"):
            batch.drop_column("created_at")
