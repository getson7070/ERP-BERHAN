"""add core module tables

Revision ID: 7c9d0e1f2g3h
Revises: 6a7b8c9d0e1f
Create Date: 2024-06-09 00:00:00 UTC
"""

from alembic import op
import sqlalchemy as sa

revision = "7c9d0e1f2g3h"
down_revision = "6a7b8c9d0e1f"
branch_labels = None
depends_on = None


def upgrade():
    for table, column in [
        ("crm_customers", "name"),
        ("hr_employees", "name"),
        ("procurement_suppliers", "name"),
        ("manufacturing_jobs", "name"),
        ("project_projects", "name"),
    ]:
        op.create_table(
            table,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column(
                "org_id", sa.Integer, sa.ForeignKey("organizations.id"), nullable=False
            ),
            sa.Column(column, sa.String(), nullable=False),
        )
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_org_isolation ON {table} USING (org_id = current_setting('erp.org_id')::int)"
        )


def downgrade():
    for table in (
        "project_projects",
        "manufacturing_jobs",
        "procurement_suppliers",
        "hr_employees",
        "crm_customers",
    ):
        op.drop_table(table)
