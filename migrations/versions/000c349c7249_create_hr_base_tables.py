"""create hr base tables

Revision ID: 000c349c7249
Revises: d4e5f6g7h8i
Create Date: 2025-09-26 17:25:36.564968
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "000c349c7249"
down_revision: Union[str, Sequence[str], None] = "d4e5f6g7h8i"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---- helpers ---------------------------------------------------------------

def _insp():
    return sa.inspect(op.get_bind())

def table_exists(name: str) -> bool:
    try:
        return name in _insp().get_table_names()
    except Exception:
        return False

def has_column(table: str, col: str) -> bool:
    try:
        return any(c["name"] == col for c in _insp().get_columns(table))
    except Exception:
        return False


# ---- migration -------------------------------------------------------------

def upgrade() -> None:
    # hr_employees (create only if missing)
    if not table_exists("hr_employees"):
        op.create_table(
            "hr_employees",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("full_name", sa.String(length=255), nullable=True),
            # created_at & employee_code added in tighten step
        )

    # hr_recruitment
    if not table_exists("hr_recruitment"):
        op.create_table(
            "hr_recruitment",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("candidate_name", sa.String(length=255), nullable=False),
            sa.Column("position", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="applied"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    # hr_performance_reviews
    if not table_exists("hr_performance_reviews"):
        op.create_table(
            "hr_performance_reviews",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("org_id", sa.Integer(), nullable=True),
            sa.Column("employee_name", sa.String(length=255), nullable=False),
            sa.Column("review_date", sa.Date(), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("comments", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    # Drop in reverse order if present
    if table_exists("hr_performance_reviews"):
        op.drop_table("hr_performance_reviews")
    if table_exists("hr_recruitment"):
        op.drop_table("hr_recruitment")
    # Only drop employees if we created it here (heuristic: no employee_code)
    if table_exists("hr_employees") and not has_column("hr_employees", "employee_code"):
        op.drop_table("hr_employees")
