"""fix rls policy to use erp.org_id"""

from alembic import op

revision = "d4e5f6g7h8i"
down_revision = "8d9e0f1a2b3c"
branch_labels = None
depends_on = None


def upgrade():
    for table in (
        "orders",
        "tenders",
        "inventory",
        "audit_logs",
        "finance_transactions",
        "inventory_items",
        "workflows",
        "crm_customers",
        "hr_employees",
        "procurement_suppliers",
        "manufacturing_jobs",
        "project_projects",
    ):
        op.execute(f"DROP POLICY IF EXISTS org_rls ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_org_isolation ON {table}")
        op.execute(
            f"CREATE POLICY org_rls ON {table} USING (org_id = current_setting('erp.org_id')::int) "
            f"WITH CHECK (org_id = current_setting('erp.org_id')::int)"
        )


def downgrade():
    for table in (
        "orders",
        "tenders",
        "inventory",
        "audit_logs",
        "finance_transactions",
        "inventory_items",
        "workflows",
        "crm_customers",
        "hr_employees",
        "procurement_suppliers",
        "manufacturing_jobs",
        "project_projects",
    ):
        op.execute(f"DROP POLICY IF EXISTS org_rls ON {table}")
        op.execute(
            f"CREATE POLICY org_rls ON {table} USING (org_id = current_setting('erp.org_id')::int) "
            f"WITH CHECK (org_id = current_setting('erp.org_id')::int)"
        )
